# aloha_fixed: getting JM1 and TITLE to build again

This is [NotExactlySiev/aloha](https://github.com/NotExactlySiev/aloha) at `03e5605` plus one branch,
**[`build-fixes`](../../tree/build-fixes)**: what it takes to build TITLE.PEX and JM1/MAIN.PEX again.
Each fix is its own commit, so the original author can cherry-pick what he wants. Nothing in the branch is
game code or data: the missing assembly is regenerated from your own disc by a script, and its output is
git-ignored.

## What was broken

The `INCLUDE_ASM` lines in `src/jm1` and `src/title` point at `asm/jm1/nonmatchings/...` and
`asm/title/...`, which are no longer in the repository (the title has no data files at all either). Some of
the C code has also moved on since that assembly was made: functions and variables were renamed, and the
old copy of libgpu/libetc in JM1 was taken out ("more libgpu removed") while the assembly still calls it.

## The fixes (branch `build-fixes`)

| Commit | File | Fix |
|---|---|---|
| 1 | `mkninja.py` | The cross-compiler prefix comes from `CROSS=` (default unchanged), and the embed rule uses `elf32-tradlittlemips` with a Linux toolchain (`mipsel-linux-gnu-`), whose binutils reject `elf32-littlemips`. |
| 2 | `src/start.s`, `src/jm1/start.s` | `v0 = 0` before the `syscall 0` in `announce_entering_main`. The syscall does not set `v0`, and the next instructions `jalr v0` when it is not 0. The rebuilt TITLE's `main` leaves `0x800F0000` there and froze at boot; the original only worked because `v0` happened to be 0. |
| 3 | `src/title/1120.c` | The menu pages written as `&(MenuPage){...}` with a flexible array member: GCC 12 stops with "non-static initialization of a flexible array member". They are named static objects now; the table `D_800EB8CC` is the same. |
| 4 | `linker/symbols.jm1.ld` | 47 old splat names the assembly uses, mapped to today's C names (`D_8010296C = entity_list_1`, `D_8013F448 = sin_lut`, `func_800E0F94 = gbuffer_get_current`, `func_800DEAD4 = GetTPage`, ...). Found in the git history and from where each name sits among the C files' functions. |
| 4 | `linker/symbols.title.ld` | `D_800EBA78 = D_800EBA7C - 4`: the C code decompresses `D_800EBA78 + 4` (the title's picture). `D_801A0FD8` as a fixed address past the title's bss. |
| 4 | `src/jm1/38F38.c` | `INCLUDE_ASM` of `func_800E8AEC`: `func_800E8A40` branches into it (`bltzal`); both were one file before. |
| 4 | `src/title/local_asm.c` | Original functions that the title's original data tables still point at, and `D_800E7FA0` (the `jt` pointer word the assembly reads). |
| 5 | `tools/buildfix/regen.py` | Regenerates the missing assembly and data from your disc (below). |

## What `tools/buildfix/regen.py` does

1. Decompresses `execs/us_jm1.pex` and `execs/us_title.pex` with knife.
2. Runs splat with every `INCLUDE_ASM` name as a function symbol, with `src/` hidden from splat. With `src/`
   present splat only writes the functions the segment's own C file includes, so everything that had moved
   to `math.c`, `weapons/`, `world1/` and so on was missing. Result: all 868 JM1 functions and the 10 TITLE
   functions the C files include.
3. Converts splat's output to this repo's `macro.inc` (no `nonmatching`/`endlabel`, no `glabel` for the
   function itself since `INCLUDE_ASM` defines it, jump-table labels global because
   `asm/jm1/data/800.rodata.s` refers to them).
4. **JM1:** links, and pulls in whatever is still undefined from the original executable: functions into
   `src/jm1/local_asm.c`, data into `src/jm1/local_data.s`, pointers in that data written as symbols. That is
   about 75 functions of the old libgpu/libetc copy, with its two driver tables (`0x80100584`, `0x8010143C`).
5. **TITLE:** adds splat's rodata and data, drops the blocks the C files now define, adds the labels the C
   files reference, turns raw pointers into symbols, drops jump tables of functions that are C now, and
   renames the labels inside `bigone` that the C files now define (those old copies are dead code).

Checked from a clean checkout: TITLE and GAMEOVER come out byte-identical to the build that was tested;
JM1 links (the same size; its regenerated pieces are in a different order).

## Build (US disc)

```sh
git checkout build-fixes
./dump_us.sh
cp build/disc_us/JM1/MAIN.PEX execs/us_jm1.pex    # the first JM1 build overwrites that file
pip install splat64                               # 0.50 was used
export CROSS=mipsel-linux-gnu-                    # optional
python3 mkninja.py us
ninja build/knife
python3 tools/buildfix/regen.py
python3 mkninja.py us
ninja build/disc_us/SCUS_941.03 build/disc_us/TITLE.PEX build/disc_us/JM1/MAIN.PEX build/disc_us/GAMEOVER.PEX
```

## Status (tested in pcsxr with its built-in BIOS)

- All four programs build and link.
- The disc boots: the Sony screen, then TITLE starts and plays the intro movie.
- **Open:** pressing Start during the intro movie with the rebuilt TITLE ends at `PC = 0` inside main's DMA
  interrupt dispatcher (a NULL DMA callback). The original TITLE with the rebuilt main skips to the menu
  fine, so the fault is in TITLE. Slowed down by breakpoints it reaches its menu loop, so it looks timing-related.
- JM1 and GAMEOVER are not tested in an emulator yet (pcsxr's built-in BIOS also goes black after
  "Game Start" with the original disc; a real BIOS is needed).
- The rebuilt TITLE is `0x18800` bytes against the original `0x15000`: it no longer fits its place on the
  disc, so a test disc has to move it (the game finds files through the ISO directory, so that works).

## Findings for the Jumping Flash CD32X port (`NOTES_CD32X.md`)

Work on the Sega CD + 32X port ([MicroNut99/JumpingFlash_CD32X](https://github.com/MicroNut99/JumpingFlash_CD32X))
turned up things that were misread, unknown or open in this decompilation. They are written up, with addresses
and formats only (no game code or data), in [`NOTES_CD32X.md`](NOTES_CD32X.md); nothing in `src/` changes.

| What was broken or unknown | What was found or fixed |
|---|---|
| Several stages' meshes looked unreadable: all of World 6's stage 1, World 6 Extra's sublevel and boss stage, three bonus sublevels | The per-mesh counts are stored as count - 1, so a count of 0 is `0xFFFFFFFF`. Read as a 32-bit number + 1 (wrapping to 0) they all load |
| The boss stages and stage 2 of worlds 3-6 had no object placement where NOTES.md expects it (`7/1`) | "Layout B": no `5/x`, `7/x`, `8/x` files; meshes `4/2`, objects `6/1`, entities `6/0` |
| Level section 0 was "entities and entity spawners (I think?)" | Its layout (a 32 x 32 grid of cells, 32-byte records: the spawn and a working copy) and the types: `0x40` carrots, `0x41` exit, `0x42` bonus things, `0x43` start, `0x44` pickups, `0x80 + n` enemy class n |
| Ground textures with colour value 0 drew as black | Colour value 0 is see-through; World 6 and World 2-2 have no ground plane at all |
| `sfx_play`'s effect numbers were opaque | High byte the VAB program, low byte the bank (`0x00` the shared `SYS_SE.VAB`, `0x1n` the world's own) and tone; the player's jumps, landing, hurt, points and the "enemy beaten" sound identified from their callers |
| The kiwi's script tables had no address in `kiwi.c`; the enemy classes of other stages and worlds were not mapped | The kiwi's tables found; every world's stage class lists, each scripted class's script and label tables, and what its own opcodes do - found the same way in all twelve `MAIN.PEX` |
| World 3's boss, World 5's boss and World 6's stage 2 boss did not fit the scripted pattern | They are hand-written state machines: World 3's boss is several parts, each a 24-state routine (patterns, timings and attacks mapped); World 5's is 15 blocks from a table of offsets, re-formed into three forms; World 6's stage 2 boss picks its moves by distance and angle |
| World 5's enemy classes seemed to be on the wrong stages, and World 6's stage 2 and 3 bosses had no class | The class lists are read through the game's own accessor (searching for a row of pointers finds a false row in World 5, one list off); an entity type under 0x40 is a class number (those two bosses are type 0x00) |
| World 5's three forms and World 6's stage 2 boss's moves were not read | Read state by state: form 1 walks and fires four, form 2 rests / drops on you / bombs / chases, form 3 spins and throws blocks; World 6's stage 2 boss leaps, goes to its spot and calls up to four hopping helpers every 64 frames |
| World 3's boss attacks looked like code | Each pattern starts hit zones that follow keyframed paths from lists filled at run time (0x8010D000-0x8010D01C): the attacks' exact moves are stage data, not code. Pattern 2's slam (36 frames in, the screen shaken) is in the code |
| The stage-end score screen was unknown | The tally (0x800D5190): 50 points a second left, 100 a heart, and a bonus from seven globals - 5 x the stage's points if never hit, 2 x if no special fired, 100 x the jewels' points if none missed, 30,000 for the carrots in order, 10,000 for three of one special |
| Beaten enemies' drops were unknown | Jewels (0x800D1CBC): a luck count decides whether an enemy bursts into 3-6 small (100) and 0-1 big (500) jewels; carrots give no points |
| A few classes and entity types did nothing visible | Sound makers (no model, a sound every spawn +8 frames: JM1 8-10, JM4 2/7, JM5 2/7); JM3 2/5 frees itself; JM5 2/5 is turning scenery |
| The special weapons' numbers | Cherry bomb 3 a use, 300 frames; twisters and rockets 10 shots, one every 8 frames; roman candle 2 |

Still open there: the per-world sound banks' remaining effects, and World 3's attack paths (stage data).

---

# Project Aloha

A (nonmatching) decompilation of Jumping Flash on PSX.
Incomplete and also kinda broken now. (I've added new bugs :D)

### Requirements

The image file for the USA or Japan version of Jumping Flash, depending
on which one you want to build. The image should be in bin/cue format.
Put it at `original/us.bin` or `original/jp.bin`. Building the European version
is not supported right now.

```sh
$ md5sum original/*.bin
f06c4a94709537b0a12af5df0889629e  original/jp.bin
4e73eb6054568a3ef88843e3d8c7d80b  original/us.bin
bfe9de682f985076dc5409ecabb7e51d  original/eu.bin
```

On Debian/Ubuntu:

```sh
apt install ninja gcc-mipsel-gnu-linux binutils-mipsel-gnu-linux
```

You also need mkpsxiso, dumpsxiso, and Python.

### Building

Dump the original disc image:

```sh
sh dump_jp.sh
# or
sh dump_us.sh
```

Generate the ninja build file:

```sh
python mkninja.py jp
# or
python mkninja.py us
```

(You will probably have to change the `cross` variable, either in the generator
script or in the final build.ninja file.)

And build the image:

```sh
ninja
```

Finally run `build/aloha_*.bin` on an emulator or real hardware.

## Disclaimer

No part of this project was done with the assistance of artificial intelligence.

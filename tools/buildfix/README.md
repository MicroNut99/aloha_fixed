# build-fixes: getting JM1 and TITLE to build again

The repository no longer has the nonmatching assembly that `INCLUDE_ASM` points at
for `jm1` and `title`, and `title` has no `asm/title/data` at all. This branch adds a
script that regenerates all of it from your own disc, plus the small source fixes
needed to link. Nothing in this branch is game code or data: everything the script
writes is listed in `.gitignore`.

Take whatever you want from it - each commit is one separate fix.

## Steps (US disc)

```
./dump_us.sh                                      # as before
cp build/disc_us/JM1/MAIN.PEX execs/us_jm1.pex    # the first JM1 build overwrites that file
pip install splat64                               # 0.50 was used
export CROSS=mipsel-linux-gnu-                    # optional, see "mkninja.py" below
python3 mkninja.py us
ninja build/knife
python3 tools/buildfix/regen.py                   # ~10 s
python3 mkninja.py us                             # picks up the generated files
ninja build/disc_us/SCUS_941.03 build/disc_us/TITLE.PEX build/disc_us/JM1/MAIN.PEX build/disc_us/GAMEOVER.PEX
```

## What `regen.py` does

1. Decompresses `execs/us_jm1.pex` and `execs/us_title.pex` with knife.
2. Runs splat with every `INCLUDE_ASM` name as a function symbol, with no `src/`
   visible to splat. With `src/` present splat only writes the functions the
   segment's own C file includes, so everything that moved to `math.c`,
   `weapons/`, `world1/` and so on was missing.
3. Converts the output to this repo's `macro.inc`: no `nonmatching`/`endlabel`,
   no `glabel` for the function itself (`INCLUDE_ASM` defines it), and jump-table
   labels (`jlabel`) made global because `asm/jm1/data/800.rodata.s` refers to them.
4. **JM1**: links and pulls in whatever is still undefined, from the original
   executable: functions go to `src/jm1/local_asm.c` (`INCLUDE_ASM`), data to
   `src/jm1/local_data.s`. Pointers in that data become symbols. That is mostly the
   old libgpu/libetc copy that commit "more libgpu removed" took out but the
   regenerated asm still calls (`LoadImage`, `SetDrawEnv`, the GPU and interrupt
   driver tables at `0x80100584` and `0x8010143C`, ...). About 75 functions.
5. **TITLE**: adds splat's rodata/data, drops the blocks the C files now define,
   adds labels the C files reference, turns raw pointers into symbols, drops jump
   tables of functions that are C now, and renames the labels inside `bigone` that
   the C files define (those old copies are dead code).

## Source fixes in this branch

| File | Fix |
|---|---|
| `linker/symbols.jm1.ld` | The old splat names the asm uses for things that have C names now (`D_8010296C = entity_list_1`, `func_800E0F94 = gbuffer_get_current`, `func_800DEAD4 = GetTPage`, ...). Found from the git history and from where each name sits in the C files. |
| `linker/symbols.title.ld` | `D_800EBA78 = D_800EBA7C - 4` (the C code reads `D_800EBA78 + 4`, the title's compressed picture); `D_801A0FD8` as a fixed address past the title's bss. |
| `src/jm1/38F38.c` | `INCLUDE_ASM` for `func_800E8AEC`: `func_800E8A40` branches to it (`bltzal`), it was part of the same old file. |
| `src/start.s`, `src/jm1/start.s` | `v0 = 0` before the `syscall 0` in `announce_entering_main`. The syscall does not set `v0`, so the `jalr v0` after it jumped to whatever was left in `v0`. The rebuilt TITLE's `main` leaves `0x800F0000` there and froze; the original code only worked because `v0` happened to be 0. |
| `src/title/1120.c` | The menu pages written as `&(MenuPage){...}` with a flexible array member: GCC 12 rejects that ("non-static initialization of a flexible array member"). They are now named static objects; the array is the same. |
| `src/title/local_asm.c` | Original functions the title's original data tables still point at, and `D_800E7FA0` (the `jt` pointer word the asm reads). |
| `mkninja.py` | `CROSS` from the environment (default unchanged), and `elf32-tradlittlemips` for the embed rule when `CROSS` is a Linux toolchain (Linux binutils reject `elf32-littlemips`). |

## Status (tested in pcsxr with its built-in BIOS)

- All four programs build and link.
- The disc boots: Sony screen, TITLE starts, the intro movie plays.
- **Open:** pressing Start during the intro movie with the rebuilt TITLE ends at
  `PC = 0` inside main's DMA interrupt dispatcher (a DMA callback that is NULL).
  The original TITLE with the rebuilt main skips to the menu fine, so it is in TITLE.
  Under the debugger, with breakpoints slowing it down, the title gets into its menu
  loop, so it looks timing-related.
- JM1 and GAMEOVER are untested in an emulator (pcsxr's built-in BIOS also goes black
  after "Game Start" with the original disc).
- The rebuilt TITLE is 0x18800 bytes against the original 0x15000, so its bss now ends
  at `0x801A0F6C`; it no longer fits the original disc extent either.

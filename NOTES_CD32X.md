# Findings from the Jumping Flash CD32X port

Worked out while porting the game to the Sega CD + 32X (MicroNut99/JumpingFlash_CD32X), checked against the
US disc (SCUS-94103). Formats and numbers only: no game data here. Addresses are the US JM1/MAIN.PEX
(loaded at 0x800B0000) unless said otherwise. These add to NOTES.md.

## Level geometry file, section 0: the entities placed in a stage

`<stage>_DAT.EAR` 7/0 (8/0 the bonus sublevel's; 6/0 in layout B, below). NOTES.md calls it "entities and entity
spawners (I think?)": it is.

```
0x00    0x30-byte head
0x30    32 x 32 u32 offsets, one per cell (0 = empty); a cell's u16 count is at 0x34 + offset
then    per cell: u16 count, count x 32 bytes:
          16-byte spawn: u8 0xFF, u8 type, s16 x, y, z (level units, y down), 8 bytes for the type
          16 bytes: a second copy of it (the game's working copy)
```

| Type | What | Count per stage |
|---|---|---|
| 0x40 | carrot (jump pod); parameter byte 0 = its number 0-3 | 4 in every stage 1 and 2 |
| 0x41 | the exit | 1 |
| 0x42 | the things to collect in a bonus sublevel | 20-30 per bonus sublevel, none elsewhere |
| 0x43 | the player's start | 1 in stage 1 (stage 2 has none) |
| 0x44 | pickups | many |
| 0x80 + n | enemy: class n of the stage's EntityClass list (JM1: `D_800FD454[stage]`, frog = 0, kiwi = 1) | |
| 0x04-0x0A | not identified (World 1 has 0x0A x 32 only there) | |

Stage 3 (the boss stage) holds one entity, type 0x80: the boss.

## Layout B

The boss stages (x-3) and stage 2 of worlds 3-6 have no 5/x, 7/x or 8/x files in their `_DAT.EAR`, and no bonus
sublevel. Meshes are 4/2 as usual; the objects (section 1's format) are 6/1; the entities (section 0) 6/0.

## Mesh files: counts of -1

The per-mesh counts are stored as count - 1, so a count of 0 is stored as 0xFFFFFFFF and must wrap (u32 + 1 = 0).
Reading them as unbounded integers is why World 6's stage 1 meshes, World 6 Extra's sublevel and boss stage,
and three other bonus sublevels looked unreadable.

## Ground textures

`<stage>_DAT.EAR` 2/3 (colours / texture). Texels whose colour value is 0 are see-through. World 6 (the sky world)
and World 2-2 have an all see-through ground: no ground plane. Their texture holds only the bonus sublevel's
"BONUS" lettering (bottom-left 64 x 64), used by the bonus sublevel.

## Sound effects

`sfx_play` (`func_800CE304`, `#define sfx_play` in jm1/sound.h) takes an effect number: high byte = the VAB
program, low byte 0x00 = the shared bank `SYS_SE.VAB`, 0x10-0x1F = the world's own bank (`VAB/Wn_m.VAB`), the
low 4 bits the tone. JM1/MAIN.PEX has 80 calls to it. Those in named functions:

| Effect | Caller | Taken to be |
|---|---|---|
| 0x0300, 0x0400, 0x0500 | `func_800DC4C4` (player) | the three jumps |
| 0x0700 (+ 0x0500) | `func_800DC9EC` (player, land) | landing |
| 0x0100 | `func_800DCEE0` (player, forward) | steps |
| 0x0600 | `func_800DCCB0` (player, movement) | falling (?) |
| 0x0C00, 0x0D00, 0x3000 | `func_800DC0CC` (player) | hurt / lost (?) |
| 0x1E00 | `func_800EB16C` (give_points) | points |
| 0x1F00 | `func_800D2F58` (an interaction) | an item taken (?) |
| 0x2000 | `func_800D2B74` (a physics function) | ? |
| 0x2100 | `func_800D1CBC` (an item dropped by an enemy) | a drop |
| 0x2400 | every World 1 enemy | an enemy beaten |
| 0xnn10-0xnn17 | each enemy's own routines | its own sounds, in the world's bank |

(?) = from the caller only, not checked by ear yet. In `SYS_SE.VAB` 0x0D00 has no tone of its own.

## Enemy scripts

Confirmed on the US disc: the frog's personality table at 0x800FE760 (three pointers: 0x800FE5BC, 0x800FE638,
0x800FE6CC) and its label table at 0x800FE710 (`frog.c`); the scripts decode with frog.c's opcodes 0-15.
`e_frog_physics` (`func_800B13BC`), which turns the frog's actions into movement, is still assembly.

The kiwi's tables (not named with an address in kiwi.c): personalities at 0x800FEAC0 (0x800FE898 the runner,
0x800FE974 the walker, 110 words apart), labels at 0x800FEA50 (28; slots outside the scripts are unused).
Spawn data for both (`FrogSpirit` / `KiwiSpirit`, little-endian): s16 health, u16 points, s16 damage (kiwi: unk),
s8 drop kind, u8 personality. Kiwi actions: 1 run (32-47 frames), 3 hop (up 4-7 units), 4 step (4-7 frames);
the physics clears the action when it is done and the script waits for that.

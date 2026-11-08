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

## World 1's enemy classes (US JM1/MAIN.PEX)

`D_800FD454` points at one class list per stage (0x800FD400, 0x800FD430, 0x800FD44C); entity type 0x80 + n is
entry n. A class: resources, a second table, class_ctor, ctor. A scripted class's ctor loads four data addresses
(the third its personality table, the fourth its label table) and sets four routines (behaviour = the script
runner, physics, interaction, one more):

| Stage / class | ctor | personalities / labels | behaviour, physics, interaction |
|---|---|---|---|
| 1 / 0 frog | 0x800B1D78 | 0x800FE760 / 0x800FE710 | 0x800B0CCC, 0x800B13BC, 0x800B1788 |
| 1 / 1 kiwi | 0x800B2FF0 | 0x800FEAC0 / 0x800FEA50 | 0x800B1F94, 0x800B25E4, 0x800B2A0C |
| 1 / 2 | 0x800B4B14 | 0x800FECBC / 0x800FEC80 | 0x800B390C, 0x800B4114, 0x800B42D4 |
| 1 / 3 | 0x800B6430 | 0x800FEF20 / 0x800FEEDC | 0x800B558C, 0x800B5ACC, 0x800B5E80 |
| 1 / 5 (shared with stage 2 / 1) | 0x800B7B58 | 0x800FF264 / 0x800FF214 | 0x800B6D28, 0x800B72F0, 0x800B7574 |
| 2 / 0 | 0x800B9068 | 0x800FF44C / 0x800FF418 | 0x800B7D5C, 0x800B8484, 0x800B8710 |
| 2 / 2 | 0x800BBD9C | 0x800FF9C4 / 0x800FF8D0 (five data addresses) | 0x800BB300, 0x800BB5D4, ... |
| 2 / 3 | 0x800BD710 | 0x800FFBA0 / 0x800FFB7C | 0x800BC3F0, 0x800BCEB4, 0x800BD158 |
| 3 / 0 the boss | 0x800C4DE8 | 0x801001F0 / 0x8010024C | 0x800C3798, 0x800C40A4, 0x800C44A8 |

Classes 1/4, 1/7-10, 2/4 and 2/5 load no script tables (simpler things: scenery, items, effects). Each scripted
class has its own copy of the script runner: opcodes 0-9 are expected to match frog.c's, the class's own ones
(10 and up) are read from its behaviour routine.

## Finding the enemy classes in any world's program

The same layout holds in all twelve MAIN.PEX (JM1 ... JM6B): a row of three pointers to the stage class lists
(two in JM5/JM5B: no list for stage 3), each an array of class records ending in 0xFFFFFFFF; a record's +8 the
class_ctor, +12 the ctor. A scripted class's ctor stores the script pointer at entity +304 (a constant: one
script, as World 1's boss; or looked up in the personality table) and the label table at +308. Its script
runner (the first routine it sets) is a switch on the vm state (li max; sltu; jump table in the .rodata at the
start of the program); opcodes 0-9 are shared, 10 and up the class's own. Their handlers sort by what they do:
three calls (player, vector length, square root) and a branch = a distance test; two random numbers stored =
a destination; volume, pan, play = its sound; an operand and a branch = compare the action; a bare operand =
speed / action; player + angle + turn + branch = facing the player within an angle.
Scripted classes found: JM1-JM2B 10 each, JM3/JM3B 10 (stages 1-2), JM4/JM4B 11, JM5/JM5B 5 (stage 1),
JM6/JM6B 6 (stages 1 and 3).

Not scripted (their ctors store no script pointer or label table; they install routines of their own - hand-
written state machines): JM3's boss (stage 3 class 0, ctor 0x800C2CF8), JM5's stage 2 classes (class 0 ctor
0x800CAB64; JM5 has no stage 3 list), JM6's stage 2 class 0 (ctor 0x800C0D98), and a few small classes (JM3
stage 1/2 class 6, JM5 stage 1 classes 5 and 7: one data address and one or two routines - effects or items).

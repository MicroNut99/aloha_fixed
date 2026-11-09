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
| 0x00-0x3F | class n of the stage's list, like 0x80 + n: World 6's stage 2 and 3 bosses are type 0x00; World 1's 0x0A (x 32, stage 1) is its class 10, scenery | |

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

The same layout holds in all twelve MAIN.PEX (JM1 ... JM6B): a row of three pointers to the stage class lists, read
by the program's first table accessor (`li 3; div; mfhi; lui / addiu`: JM1's `D_800FD454[n % 3]` at 0x800B0AD4; JM5's
row 0x8010212C), each an array of class records ending in 0xFFFFFFFF (0 = an unused class number: JM5 stage 1's
class 2); a record's +8 the
class_ctor, +12 the ctor. A scripted class's ctor stores the script pointer at entity +304 (a constant: one
script, as World 1's boss; or looked up in the personality table) and the label table at +308. Its script
runner (the first routine it sets) is a switch on the vm state (li max; sltu; jump table in the .rodata at the
start of the program); opcodes 0-9 are shared, 10 and up the class's own. Their handlers sort by what they do:
three calls (player, vector length, square root) and a branch = a distance test; two random numbers stored =
a destination; volume, pan, play = its sound; an operand and a branch = compare the action; a bare operand =
speed / action; player + angle + turn + branch = facing the player within an angle.
Scripted classes found: JM1-JM2B 10 each, JM3/JM3B 10 (stages 1-2), JM4/JM4B 11, JM5/JM5B 9 (stages 1-2),
JM6/JM6B 6 (stages 1 and 3).  (Searching for any row of list pointers instead finds a false one in JM5, one list
off: its stage 2's classes then look like stage 1's and stage 3 seems to have none.)

Not scripted (their ctors store no script pointer or label table; they install routines of their own - hand-
written state machines): JM3's boss (stage 3 class 0, ctor 0x800C2CF8), JM5's boss (stage 3 class 0, ctor
0x800CAB64), JM6's stage 2 class 0 (ctor 0x800C0D98: World 6's stage 2 is a boss stage, its one entity), and a few
small classes (JM3 stage 1/2 class 6, JM5 stage 1 classes 5 and 7: one data address and one or two routines -
effects or items).

### JM3's boss (stage 3 class 0, ctor 0x800C2CF8): where its logic is

The ctor installs two short routines - entity +36 = 0x800C2C4C, +68 = 0x800C2CC8 (a few branches and one call
each: wrappers) - calls 0x800C21C8 and 0x800E1678 / 0x800E16B0 / 0x800DF564 / 0x800DF530, keeps its state in
globals at 0x800FF3D0-0x800FF414, and calls 0x800C2AD4 in a loop (counting s2 up): it builds the boss out of
several parts, each an entity of its own. The behaviour is in those parts' routines (from 0x800C2AD4) and the
globals they share - the next thing to read.

Its parts (0x800C2AD4 builds each): three routines - +36 = 0x800C183C, +68 = 0x800C21E8, +52 = 0x800C29DC.
0x800C183C is a hand-written state machine, not a script runner: a switch on the component state (0-23, jump
table at 0x800B0580) whose cases set the next state and call routines; it reads the part's number (+252) and
a shared bit mask of the parts (global at 0x800FF3FC, a bit per part: cleared as a part is lost). Twenty-four
states to read, one by one.

The 24 states, by what they set (the component state at +0 of the component, its counter at +4, the entity's
+262 = the attack pattern through 0x800C10E8): 0-1 setup; 2-3 pattern 4, 64 frames; 4-6 a pause; 7-9 pattern 1,
160 frames (+260 = 88); 10-11 wait 76; 12-15 pattern 2, 96 then 156 frames; 16 the part lost; 18-21 pattern 3,
96 then 132 frames (+260 = 60); 22-23 wait 76. Each pattern's moves are in 0x800C1300 / 0x800C1508 /
0x800C1570 / 0x800C0008 (not read yet).

The pattern routines: 0x800C1300 (every pattern) steers the part at the player - an angle (0x800C9C34), a turn of
at most 0x20 (0x800CC448 / 0x800CC6C8, stored at +164) - and eases its velocity (+104 x, +112 z, +120 y; through
0x800D86CC). 0x800C1508 (pattern 1) counts +260 down and fires through 0x800C0548, the counter set to 12 after
each shot (88 before the first: state 8). 0x800C1570 (pattern 3) throws one object up at -800 through 0x800C0A98
(+260 = 60 before it: state 20). 0x800C0008 (state 6, the end of pattern 4) an effect through 0x800E17F0.

0x800C1300 turns the part's ring toward an angle given in a1 (0 or 0x800 of 4096) at 0x40 a frame, returning
non-zero until it is there: pattern 4 (states 2-3) turns it half round, patterns 1 and 2 (states 8, 13) back to 0.
Pattern 2 is a slam: 96 frames rising, then a 156-frame animation; 36 frames into it a bit in 0x8010F404 is set for
the part, the screen is shaken (0x800D1540 points 0x8010CA94 at a shake table) and sound 0x2F17 plays.

Each pattern also starts its hit zones (0x800C10E8, called with two lists): one child entity per entry of the
first list (update 0x800C0CDC, interaction 0x800C104C; +264 the entry, +268 the second list, +272 the boss part).
The child follows a keyframed path - positions interpolated between the boss's animation frames (+72 / +86) - and
is harmful only in the frame ranges of the second list (+100). The lists are pointers at 0x8010D000-0x8010D01C
(pattern 4: 0x8010D008 / 0x8010D01C; 1: 0x8010D010; 2: 0x8010D014; 3: 0x8010D018). Nothing in JM3's program
writes them: they are filled at run time from the stage's data, so the exact moves of the attacks are there,
not in the code.

### JM5's boss (stage 3 class 0, ctor 0x800CAB64)

The spawn's health (+8, 14000) goes to a global (0x80107B68, also 0x80107B60), its points x 10 to 0x80107B78. The
ctor builds 15 parts (0x800C0120 each, routines 0x800BFD60 / 0x800BFE2C / 0x800BFFB0), placed by a table at
0x8010485C (8 bytes each: s16 x, y, z, 0): the middle, the 8 corners at +-276, the 6 face middles at +-264 - a block
of 15; part 0 is raised 192, the others 72. The boss's own routine (+20 = 0x800C9824) is a 9-state machine (jump
table 0x800B071C): 0-1 setup (0x800C1404); 2 the fight, until the health global is 0, then the 15 part slots (0x801098D0,
36 bytes each) cleared; 3 the parts placed again in one of three forms (a global at 0x80107B48, 0-2: each part
through 0x800BF9A8, which turns its offset (0x800D1300), then 0x800BFA60 / 0x800BFBD0 / 0x800BFB18 - the form's
heights); 4 wait for the 15, a sound (0x4A16, 0x800D2E38); 5 the form's own routine (0x800C41F8 / 0x800C8958 /
0x800C62C0, not read); 6-8 as 2-4 again.

The three forms (0x800C41F8 / 0x800C8958 / 0x800C62C0 build the form's entity: +36 its update, +304 / +308 its
animation sequences, pairs of (animation, frames) ending in -1, e.g. 0x80104CE8 / 0x80104DCC for form 1):

- **Form 1** (update 0x800C3570, 14 states, jump table 0x800B0534): walks at the player, turning 0x18 of 4096 a
  frame, for 114 + random / 8 frames, a step sound (0x4B10) every 54 frames; then looks up (+156 = -64) for 40
  frames and fires 4 shots 32 frames apart (0x800C30B4: from 0x234 in front of it, sound 0x4B12); again. States
  10-13: its hit and end reactions (animations 4 / 5, 48 frames; 0x800BF944).
- **Form 2** (update 0x800C7B40, 22 states, jump table 0x800B067C): hovers about a target height +276
  (0x800C74E8: 0x400 a frame toward it, at most 0xC000). After each animation (state 3 switches on +252) it goes
  to: a rest (64 + random / 8 frames); a drop on the player (64 frames rising and turning, then gravity 0x1800 to
  at most 0x30000; 0x800C7758: 30 damage to a player under it; landing: sound 0x4B11, the screen shaken,
  a bounce up 3); bombs from high (+276 = -2560; 2 + random / 32 bombs 24 frames apart, 0x800C7600: dropped from
  0xC0 under it); a chase (288 frames, turn 0x30, speed up 2048 a frame to 0xE000, sound 0x4A1B every 96).
- **Form 3** (update 0x800C5504, 12 states, jump table 0x800B05DC): rises (3072 a frame, to at most -8192) and
  spins up for 64 frames (+152 / +156 the turn rates, random accelerations clamped to +-0x72000), spins 320
  frames throwing blocks (0x800C4F18: every 4 frames, a chance of 240 in 256), a spin sound (0x4B13) as fast as
  it turns, then spins down and rests 48.

The order in which form 2 picks its moves is set by its animation sequence (+304), not by code.

### JM6's stage 2 boss (class 0, ctor 0x800C0D98)

Routines: +20 = 0x800BF19C, +36 = 0x800BFE04, +68 = 0x800C0598, +52 = 0x800C0B74. 0x800BF19C counts +268 down and
switches on the state (23 states, jump table 0x800B03A0): state 0 waits 80 frames; state 2 picks the next state by the
player's distance (0x800CA744; 96, 128, 192) and angle (-127, -512, -1024): states 5, 7, 9, 12 or 22.

The states: 3 waits distance / 8, then back to 2; 5 and 7 give its physics (+36) action 4 or 1 (+258), then wait
distance / 4 + 64 (or + 32); 9, 12, 13 actions 2 and 5, waiting for +256 to match and then for it to be 0. Its
physics' jumps: up at 16 a frame (lui 0xFFFF) and at 64 (0xFFFC). States 15-22 call its helpers: it goes to its
spot (0x800C99C0: x 0, z 0x83E), leaps (action 2), then state 22 calls 0x800BE964 every 64 frames, four times, and
state 19 sets +268 = 600 (the wait before it does so again).

The helper (0x800BE964 makes one; at most 4 at once, counted in 0x8010CAEC): it appears at (0, 0, 0x81E), +92 = 500,
update 0x800BE220: 8 frames still; a jump (sound 0x4C12) up at (its distance to the player + 384) / 16 a frame,
12 a frame forward (+172), gravity 0x1000 a frame (+132), the fall at most 0x18000; off a wall a bounce up 3; on the
ground 12 frames (sound 0x0700), then again.


## The stage-end tally (JM1)

0x800D5190 (8 states, jump table 0x800B0844) counts three amounts into the score in turn (states 3-5, each through
0x800D5038: a step every other frame, the step 10 times bigger after 10 steps when the rest divides by it, at most
99999; sound 0x2C00 every 3 frames; 0x1F00 at the end). The amounts are worked out first (0x8011F818 + 8 / + 20 / + 32):

| | routine | amount |
|---|---|---|
| time | 0x800DB798 | the time left in seconds, rounded up, x 50 |
| hearts | 0x800DB800 | the player's +92 x 100 |
| bonus | 0x800DB6B4 | below; at most 9,999,999 |

The bonus, from globals the stage start clears (0x800DB670):

| global | set by | meaning | in the bonus |
|---|---|---|---|
| 0x80102B8C | 0x800DB8B8, from `give_points` (0x800EB16C) | the stage's own points (A) | 5 x A if 0x80102B6C is 0; 2 x A if 0x80102B74 is 0 |
| 0x80102B6C | 0x800DB87C, from 0x800DC238 (a hit taken: sound 0x0D00) | hurt | |
| 0x80102B74 | 0x800DB890, from 0x800FD150 (a special weapon fired) | special used | |
| 0x80102B84 | 0x800DB8D8, from 0x800D3070 (a jewel taken) | the jewels' points (B) | 100 x B if 0x80102B7C is 0 |
| 0x80102B7C | 0x800DB8A4, from 0x800D2FCC (a jewel left 720 frames) | a jewel missed | |
| 0x80102B94 | 0x800DB8F8, from 0x800D2534 (a carrot taken: its id, spawn +8) | the carrots' order: id = count -> count + 1, else -1 | 30,000 if it is 4 |
| 0x80102B9C | 0x800DB928, from 0x800ED2C4 (the special weapon list) | 10,000 the first time the three held are the same weapon (a bit per weapon) | added |

A carrot (spawn type 0x40, ctor 0x800D2618; the type table at 0x800B07A8: 0x40 carrot, 0x41 0x800D2A8C, 0x42 0x800D3D28,
0x43 0x800D45C4, 0x44 the pickups 0x800D2184) gives no points of its own: a message (0x800EE26C) and, at the fourth,
sound 0x2300 and voice 0x3F00.

## Jewels from beaten enemies (JM1 0x800D1CBC)

When an enemy is beaten: a random number under 65 - nothing (or an item: 0x800D1868, at most 11 at once); else a luck
count (0x801029DC) goes up by 32 + a random 0-47; while it stays under 256 the enemy bursts into 3 + random / 64 small
jewels and random / 128 big ones (0x800D35A8, each one 0x800D3378: thrown up at 20 a frame in a random direction);
over 256 the count wraps (& 0xFF). A jewel is worth 100, or 500 (+74 = 2); taken: sound 0x1F00, its points, and
0x800DB8D8. One left 720 frames is gone, and 0x800DB8A4 is set.

## Special weapons (JM1)

From the ctors: the cherry bomb (0x800FB4C8) three at a use (slti 3), each +92 = 300 frames, the blast sound 0x1600;
the twisters (0x800FCF30) and the rockets (0x800FA0BC) 10 shots (+252 under 10), one every 8 frames (+254 = 8), at
most 16 out, the twisters' angle spread from 0x8010315C; the roman candle (0x800FC40C) two (0x800FC244 with +-1),
sound 0x1800.

## Classes that only make a sound, and two that do nothing

JM4 stage 2 class 7 (ctor 0x800C575C) has no model: its update (0x800C55B0) counts the spawn's word +8 down and
plays 0x3E10 at its place, then keeps the voice's volume by the distance. The same kind: JM1's classes 8-10 (0x0D10,
0x0E10, 0x0C10) and JM5 stage 2 class 7 (0x4911). JM3 stage 2 class 5 (ctor 0x800BE034) frees itself at once.
JM5 stage 2 class 5 (ctor 0x800BDC74) is scenery: model 0x69, turned through the keyframes at 0x80104600.

## Stage time limits

The level timer (`func_800EB354` sets it, clamped to 0..0x34BBF, in 1/60 s; `func_800EB3A0` the second one)
is started from `func_800E3CD8`: the program's second stage-table accessor (JM1 0x800B0C58: `li 3; div; mfhi`,
row 0x800FE510, 8 bytes a stage: the stage's record, its bonus sublevel's) gives a record whose +192 is the limit.
First-round worlds: 10:00 a stage (World 2 stage 2: 5:00), 1:00 a bonus sublevel. Extra worlds (JMnB): 3:00-5:00.

## Pickups (type 0x44)

Spawn byte 0 is the kind, 1-10 (kept at +74; its mesh is the pickup mesh + kind). Taken (`func_800D207C` ->
`func_800D156C(kind)`, a switch on kind - 1, jump table 0x800B07C0): 1 a heart back (health routines
0x800EBE5C, sound 0x1D00); 2 `func_800EC058(1)` (more health) and the hearts back (0x1D00); 3 `func_800ED60C`
(sets 0x80102EFC: the time stop, timestop.c); 4 `func_800EDDBC` (sets 0x80102F3C: "seizure.c", a flash);
5 `func_800ED344(1)` (a life, sound 0x1E00); 6 `func_800EB3EC(0x708)` (30 seconds more, sound 0x1C00); 7-10
`func_800ED26C` (a special weapon). Kind 5 is taken once; the others come back. The text shown with each is
message 0x3900-0x3D00.

## Movies

`MOVIE/*.STR`: 512 x 208, 15 a second, XA sound 37,800 Hz stereo. Their MDEC frames say version 1 in the frame
header (+6); the bitstream is version 2's (ffmpeg decodes them once that word says 2).

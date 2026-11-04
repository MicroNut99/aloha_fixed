#!/usr/bin/env python3
"""Regenerate the assembly and data that JM1 (World 1) and TITLE need, from your own disc.

Run from the repository root after dump_us.sh and one extra copy:

    cp build/disc_us/JM1/MAIN.PEX execs/us_jm1.pex   # before the first build overwrites it
    ninja build/knife
    python3 tools/buildfix/regen.py

What it does (nothing here contains game code; everything it writes is git-ignored):
  1. decompresses execs/us_jm1.pex and execs/us_title.pex with knife;
  2. runs splat on each with every INCLUDE_ASM name as a symbol, so each function the
     C files include gets its own .s file (a src/ tree is hidden from splat so that it
     emits every function, not only the ones the C file of that segment includes);
  3. converts splat 0.3x+ output to this repo's macro.inc (no nonmatching/endlabel,
     no glabel for the function itself, jump-table labels made global);
  4. JM1: links, and for every name still undefined pulls the original code
     (INCLUDE_ASM into src/jm1/local_asm.c) or data (src/jm1/local_data.s) from the
     decompressed executable. Pointers inside that data are written as symbols;
  5. TITLE: adds splat's rodata/data, drops blocks the C files now define, adds labels
     the C files reference, turns raw pointers into symbols, and renames labels inside
     the big hand-merged function that the C files now define.

Needs: splat64 (pip), a MIPS cross toolchain (set CROSS=, default mipsel-linux-gnu-).
"""
import os, re, sys, glob, struct, shutil, subprocess, tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CROSS = os.environ.get('CROSS', 'mipsel-linux-gnu-')
W = os.path.join(ROOT, 'build', 'regen')

def sh(cmd, **kw):
    return subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True, text=True, **kw)

def decompress(pex, out):
    r = sh([os.path.join(ROOT, 'build', 'knife'), 'pex', 'decompress', pex, out])
    if r.returncode: sys.exit(f'knife failed on {pex}: {r.stderr}')

def include_asm_names(srcdir, module):
    names = {}
    for f in glob.glob(os.path.join(ROOT, 'src', srcdir, '**', '*.c'), recursive=True):
        for line in open(f, errors='replace'):
            m = re.match(r'\s*INCLUDE_ASM\("asm/' + module + r'/nonmatchings/([^"]+)",\s*(\w+)\)', line)
            if m: names[m.group(2)] = m.group(1)
    return names

def convert(src, dst, keep_self=False):
    """splat output -> this repo's style"""
    for root, _, fs in os.walk(src):
        for f in fs:
            if not f.endswith('.s'): continue
            name = f[:-2]; out = []
            for l in open(os.path.join(root, f)):
                s = l.strip()
                if s.startswith(('nonmatching ', 'endlabel ', 'enddlabel ')): continue
                if s == f'glabel {name}' and not keep_self: continue
                m = re.match(r'(jlabel|alabel|dlabel)\s+(\S+)', s)
                if m: out.append(f'glabel {m.group(2)}\n'); continue
                out.append(l)
            d = os.path.join(dst, os.path.relpath(root, src)); os.makedirs(d, exist_ok=True)
            open(os.path.join(d, f), 'w').writelines(out)

def run_splat(yaml_text, exe, symbols, workdir):
    os.makedirs(workdir, exist_ok=True)
    shutil.copy(exe, os.path.join(workdir, 'target.exe'))
    open(os.path.join(workdir, 'symbol_addrs.txt'), 'w').write(symbols)
    open(os.path.join(workdir, 'cfg.yaml'), 'w').write(yaml_text)
    r = sh([sys.executable, '-m', 'splat', 'split', 'cfg.yaml'], cwd=workdir)
    # splat also writes a linker script we do not use; an error there is harmless
    if not glob.glob(os.path.join(workdir, 'asm', '*', 'nonmatchings')):
        sys.exit('splat failed:\n' + r.stdout[-3000:] + r.stderr[-3000:])

def regen_ninja():
    sh([sys.executable, 'mkninja.py', 'us'], cwd=ROOT)

def ninja(target):
    r = sh(['ninja', '-C', ROOT, target])
    return r.stdout + r.stderr, 'FAILED' not in r.stdout and r.returncode == 0

# ---------------------------------------------------------------- JM1
JM1_YAML = """options:
  platform: psx
  basename: jm1
  base_path: .
  target_path: target.exe
  asm_path: asm/jm1
  asset_path: assets/jm1
  src_path: src/jm1
  build_path: build
  compiler: GCC
  symbol_addrs_path: symbol_addrs.txt
  use_legacy_include_asm: no
  migrate_rodata_to_functions: no
  section_order: [".rodata", ".text", ".data", ".bss"]
segments:
  - [0x0, header]
  - name: jm1
    type: code
    start: 0x800
    vram: 0x800B0000
    subsegments:
      - [0x800, rodata]
      - [0x1268, c, "1268"]
      - [0x173B4, c, "173B4"]
      - [0x38F38, c, "38F38"]
      - [0x4DC00, data]
  - [0x53800]
"""
JM1_BASE = 0x800B0000 - 0x800
NAMED_JM1 = {'decompress_lz1_c': 0x800E8F08}

def jm1():
    exe = os.path.join(W, 'JM1.exe')
    decompress(os.path.join(ROOT, 'execs', 'us_jm1.pex'), exe)
    img = open(exe, 'rb').read()
    names = include_asm_names('jm1', 'jm1')
    syms = []
    for n in names:
        a = NAMED_JM1.get(n)
        if a is None and re.fullmatch(r'func_[0-9A-F]{8}', n): a = int(n[5:], 16)
        if a: syms.append(f'{n} = 0x{a:08X}; // type:func')
    sp = os.path.join(W, 'splat_jm1')
    shutil.rmtree(sp, ignore_errors=True)
    run_splat(JM1_YAML, exe, '\n'.join(syms) + '\n', sp)
    dst = os.path.join(ROOT, 'asm', 'jm1', 'nonmatchings')
    shutil.rmtree(dst, ignore_errors=True)
    convert(os.path.join(sp, 'asm', 'jm1', 'nonmatchings'), dst)
    have = {os.path.basename(p)[:-2]: p.split('/')[-2] for p in glob.glob(dst + '/*/*.s')}
    missing = [n for n in names if n not in have]
    if missing: sys.exit(f'splat did not produce: {missing[:10]}')
    print(f'jm1: {len(have)} functions written, {len(names)} included by the C files')
    jm1_closure(img, have)

def is_text(b):
    n = b.find(b'\0')
    return n > 0 and all(32 <= c < 127 or c in (9, 10) for c in b[:n])

def jm1_closure(img, have):
    """pull original code/data for names the link still needs"""
    loc = os.path.join(ROOT, 'src', 'jm1', 'local_asm.c')
    dat = os.path.join(ROOT, 'src', 'jm1', 'local_data.s')
    base_c = open(loc).read() if os.path.exists(loc) else ''
    open(dat, 'w').write('.include "macro.inc"\n/* generated by tools/buildfix/regen.py from your disc - do not commit */\n')
    regen_ninja()
    text_lo, text_hi = 0x800B0000 + 0x1268 - 0x800, 0x800B0000 + 0x4DC00 - 0x800
    end_img = 0x800B0000 + len(img) - 0x800
    # every data label the repo's data files already define, by address
    known = set()
    for f in glob.glob(os.path.join(ROOT, 'asm', 'jm1', 'data', '*.s')):
        t = open(f).read()
        for m in re.finditer(r'glabel \w+\n\s*/\* [0-9A-F]+ ([0-9A-F]{8})', t): known.add(int(m.group(1), 16))
        for m in re.finditer(r'glabel D_([0-9A-F]{8})', t): known.add(int(m.group(1), 16))
    refs = set(int(x, 16) for p in glob.glob(os.path.join(ROOT, 'asm/jm1/nonmatchings/*/*.s'))
               for x in re.findall(r'D_([0-9A-F]{8})', open(p).read()))
    bounds = sorted(known | refs)
    done = set()
    def word_sym(w):
        if w == 0: return '0'
        if text_lo <= w < text_hi:
            return f'func_{w:08X}' if f'func_{w:08X}' in have else f'.L{w:08X}'
        if 0x800B0000 <= w < end_img or 0x80100000 <= w < 0x80150000: return f'D_{w:08X}'
        return f'0x{w:08X}'
    for it in range(40):
        out, ok = ninja('build/jm1.elf')
        if ok:
            print(f'jm1: links after {it} rounds'); return
        und = sorted(set(re.findall(r"undefined reference to `([^']+)'", out)))
        if not und: sys.exit(out[-3000:])
        addc, addd = [], []
        for n in und:
            if n in done: continue
            done.add(n)
            if n.startswith('func_'):
                if n not in have: sys.exit(f'no asm for {n}')
                addc.append(f'INCLUDE_ASM("asm/jm1/nonmatchings/{have[n]}", {n});\n'); continue
            if not n.startswith('D_'): sys.exit(f'cannot resolve {n}:\n' + out[-2000:])
            X = int(n[2:], 16)
            nxt = min([b for b in bounds if b > X] + [X + 0x1000]); size = nxt - X
            rodata = X < 0x800B0000 + 0x1268 - 0x800
            if X < end_img:
                b = img[X - JM1_BASE:X - JM1_BASE + size]
                if rodata and is_text(b):
                    size = (b.find(b'\0') + 4) & ~3; b = b[:size]
                body = ''
                words = [struct.unpack_from('<I', b, k)[0] for k in range(0, len(b) - 3, 4)]
                if not rodata and len(b) % 4 == 0 and any(0x800B0000 <= w < 0x80150000 for w in words):
                    body = ''.join(f'\t.word {word_sym(w)}\n' for w in words)
                else:
                    body = ''.join(f'\t.byte {", ".join(str(c) for c in b[i:i+16])}\n' for i in range(0, len(b), 16))
                addd.append(f'\n.section {".rodata" if rodata else ".data"}\n.align 2\nglabel {n}\n{body}')
            else:
                addd.append(f'\n.section .bss\n.align 2\nglabel {n}\n\t.space {hex(size)}\n')
        if not addc and not addd: sys.exit('jm1: no progress:\n' + out[-3000:])
        if addc:
            if not base_c:
                base_c = '/* original code the regenerated asm still calls (regen.py) */\n#include "common.h"\n'
            base_c += ''.join(addc); open(loc, 'w').write(base_c)
            for o in glob.glob(os.path.join(ROOT, 'build', 'jm1', 'local_asm.c.o')): os.remove(o)
        open(dat, 'a').writelines(addd)
        regen_ninja()
    sys.exit('jm1: did not converge')

# ---------------------------------------------------------------- TITLE
TITLE_SYMS = ['func_800E15FC', 'func_800E189C', 'func_800E12B4', 'func_800E1384', 'func_800E1418',
              'func_800E14CC', 'func_800E1C24', 'func_800E1FB8', 'func_800E3168']

def c_defined(srcdir):
    names = set()
    for f in glob.glob(os.path.join(ROOT, 'src', srcdir, '**', '*.c'), recursive=True):
        for m in re.finditer(r'^[A-Za-z_][\w \*]*?\b(\w+)\s*\([^;{]*\)\s*\{', open(f, errors='replace').read(), re.M):
            names.add(m.group(1))
    return names

def title():
    exe = os.path.join(W, 'TITLE.exe')
    decompress(os.path.join(ROOT, 'execs', 'us_title.pex'), exe)
    y = open(os.path.join(ROOT, 'splat.title.yaml')).read()
    y = re.sub(r'target_path:.*', 'target_path: target.exe', y)
    y = re.sub(r'symbol_addrs_path:.*', 'symbol_addrs_path: symbol_addrs.txt', y)
    y = re.sub(r'(\n\s*- name:)\s*\n', r'\1 title\n', y)
    syms = ''.join(f'{n} = 0x{n[5:]}; // type:func\n' for n in TITLE_SYMS)
    syms += 'bigone = 0x800E5818; // type:func size:0x1EBC\n'
    sp = os.path.join(W, 'splat_title'); shutil.rmtree(sp, ignore_errors=True)
    run_splat(y, exe, syms, sp)
    for d in ('nonmatchings', 'data'):
        shutil.rmtree(os.path.join(ROOT, 'asm', 'title', d), ignore_errors=True)
    convert(os.path.join(sp, 'asm', 'title', 'nonmatchings'), os.path.join(ROOT, 'asm', 'title', 'nonmatchings'))
    convert(os.path.join(sp, 'asm', 'title', 'data'), os.path.join(ROOT, 'asm', 'title', 'data'), keep_self=True)
    # labels inside bigone that the C files now define
    big = os.path.join(ROOT, 'asm/title/nonmatchings/1120/bigone.s')
    defined = c_defined('title')
    t = open(big).read()
    for n in defined:
        t = re.sub(r'^glabel ' + re.escape(n) + r'$', n + '_bigone_old:', t, flags=re.M)
    open(big, 'w').write(t)
    # orphan jump tables of functions that are C now
    p = os.path.join(ROOT, 'asm/title/data/800.rodata.s'); t = open(p).read()
    have = set(os.path.basename(x)[:-2] for x in glob.glob(os.path.join(ROOT, 'asm/title/nonmatchings/1120/*.s')))
    incl = set(include_asm_names('title', 'title')) | {'bigone'}
    labels_in_included = set()
    for n in incl:
        f = os.path.join(ROOT, f'asm/title/nonmatchings/1120/{n}.s')
        if os.path.exists(f): labels_in_included |= set(re.findall(r'glabel (\.L[0-9A-F]{8})', open(f).read()))
    blocks = re.split(r'(?=^glabel )', t, flags=re.M); keep = []
    for b in blocks:
        ls = re.findall(r'\.word (\.L[0-9A-F]{8})', b)
        if b.startswith('glabel jtbl_') and ls and not set(ls) <= labels_in_included: continue
        keep.append(b)
    open(p, 'w').write(''.join(keep))
    title_pointers()
    regen_ninja()
    title_fixups()

def title_pointers():
    fs = glob.glob(os.path.join(ROOT, 'asm/title/data/*.s'))
    txt = {f: open(f).read() for f in fs}
    for X in sorted(set(m for t in txt.values() for m in re.findall(r'\.word 0x(800[EF][0-9A-F]{4})', t))):
        for f, t in txt.items():
            mm = re.search(r'^[ \t]*/\* [0-9A-F]+ ' + X + r'\b[^\n]*\n', t, re.M)
            if mm:
                if f'glabel D_{X}\n' not in t: t = t[:mm.start()] + f'glabel D_{X}\n' + t[mm.start():]
                txt[f] = t; break
        else:
            continue
        for f in txt: txt[f] = txt[f].replace(f'.word 0x{X}', f'.word D_{X}')
    for f, t in txt.items(): open(f, 'w').write(t)

def title_fixups():
    D = os.path.join(ROOT, 'asm/title/data')
    for it in range(20):
        out, ok = ninja('build/title.elf')
        if ok: print(f'title: links after {it} rounds'); return
        multi = sorted(set(re.findall(r"multiple definition of `([^']+)'", out)))
        und = sorted(set(re.findall(r"undefined reference to `([^']+)'", out)))
        changed = False
        for n in multi:
            for f in glob.glob(D + '/*.s'):
                t = open(f).read()
                if f'glabel {n}\n' in t:
                    open(f, 'w').write(re.sub(r'glabel ' + re.escape(n) + r'\n(?:(?!glabel )[^\n]*\n)*', '', t, count=1)); changed = True
        for n in und:
            m = re.fullmatch(r'D_([0-9A-F]{8})', n)
            if not m: continue
            for f in glob.glob(D + '/*.s'):
                t = open(f).read()
                mm = re.search(r'^[ \t]*/\* [0-9A-F]+ ' + m.group(1) + r'\b[^\n]*\n', t, re.M)
                if mm and f'glabel {n}\n' not in t:
                    open(f, 'w').write(t[:mm.start()] + f'glabel {n}\n' + t[mm.start():]); changed = True; break
        if not changed: sys.exit('title: unresolved:\n' + out[-3000:])
    sys.exit('title: did not converge')

if __name__ == '__main__':
    os.makedirs(W, exist_ok=True)
    if not os.path.exists(os.path.join(ROOT, 'build', 'knife')): sys.exit('run "ninja build/knife" first')
    for p in ('execs/us_jm1.pex', 'execs/us_title.pex'):
        if not os.path.exists(os.path.join(ROOT, p)): sys.exit(f'missing {p} (see the top of this file)')
    which = sys.argv[1:] or ['jm1', 'title']
    if 'jm1' in which: jm1()
    if 'title' in which: title()

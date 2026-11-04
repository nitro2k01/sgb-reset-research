#!/usr/bin/env python3
# 65816 recursive disassembler with M/X tracking, LoROM
import sys, collections
T = """
00 brk imm8|01 ora dpxi|02 cop imm8|03 ora sr|04 tsb dp|05 ora dp|06 asl dp|07 ora dpil|08 php imp|09 ora immm|0a asl acc|0b phd imp|0c tsb abs|0d ora abs|0e asl abs|0f ora long
10 bpl rel|11 ora dpiy|12 ora dpi|13 ora sriy|14 trb dp|15 ora dpx|16 asl dpx|17 ora dpily|18 clc imp|19 ora absy|1a inc acc|1b tcs imp|1c trb abs|1d ora absx|1e asl absx|1f ora longx
20 jsr abs|21 and dpxi|22 jsl long|23 and sr|24 bit dp|25 and dp|26 rol dp|27 and dpil|28 plp imp|29 and immm|2a rol acc|2b pld imp|2c bit abs|2d and abs|2e rol abs|2f and long
30 bmi rel|31 and dpiy|32 and dpi|33 and sriy|34 bit dpx|35 and dpx|36 rol dpx|37 and dpily|38 sec imp|39 and absy|3a dec acc|3b tsc imp|3c bit absx|3d and absx|3e rol absx|3f and longx
40 rti imp|41 eor dpxi|42 wdm imm8|43 eor sr|44 mvp mv|45 eor dp|46 lsr dp|47 eor dpil|48 pha imp|49 eor immm|4a lsr acc|4b phk imp|4c jmp abs|4d eor abs|4e lsr abs|4f eor long
50 bvc rel|51 eor dpiy|52 eor dpi|53 eor sriy|54 mvn mv|55 eor dpx|56 lsr dpx|57 eor dpily|58 cli imp|59 eor absy|5a phy imp|5b tcd imp|5c jml long|5d eor absx|5e lsr absx|5f eor longx
60 rts imp|61 adc dpxi|62 per rell|63 adc sr|64 stz dp|65 adc dp|66 ror dp|67 adc dpil|68 pla imp|69 adc immm|6a ror acc|6b rtl imp|6c jmp absi|6d adc abs|6e ror abs|6f adc long
70 bvs rel|71 adc dpiy|72 adc dpi|73 adc sriy|74 stz dpx|75 adc dpx|76 ror dpx|77 adc dpily|78 sei imp|79 adc absy|7a ply imp|7b tdc imp|7c jmp absxi|7d adc absx|7e ror absx|7f adc longx
80 bra rel|81 sta dpxi|82 brl rell|83 sta sr|84 sty dp|85 sta dp|86 stx dp|87 sta dpil|88 dey imp|89 bit immm|8a txa imp|8b phb imp|8c sty abs|8d sta abs|8e stx abs|8f sta long
90 bcc rel|91 sta dpiy|92 sta dpi|93 sta sriy|94 sty dpx|95 sta dpx|96 stx dpy|97 sta dpily|98 tya imp|99 sta absy|9a txs imp|9b txy imp|9c stz abs|9d sta absx|9e stz absx|9f sta longx
a0 ldy immx|a1 lda dpxi|a2 ldx immx|a3 lda sr|a4 ldy dp|a5 lda dp|a6 ldx dp|a7 lda dpil|a8 tay imp|a9 lda immm|aa tax imp|ab plb imp|ac ldy abs|ad lda abs|ae ldx abs|af lda long
b0 bcs rel|b1 lda dpiy|b2 lda dpi|b3 lda sriy|b4 ldy dpx|b5 lda dpx|b6 ldx dpy|b7 lda dpily|b8 clv imp|b9 lda absy|ba tsx imp|bb tyx imp|bc ldy absx|bd lda absx|be ldx absy|bf lda longx
c0 cpy immx|c1 cmp dpxi|c2 rep imm8|c3 cmp sr|c4 cpy dp|c5 cmp dp|c6 dec dp|c7 cmp dpil|c8 iny imp|c9 cmp immm|ca dex imp|cb wai imp|cc cpy abs|cd cmp abs|ce dec abs|cf cmp long
d0 bne rel|d1 cmp dpiy|d2 cmp dpi|d3 cmp sriy|d4 pei dp|d5 cmp dpx|d6 dec dpx|d7 cmp dpily|d8 cld imp|d9 cmp absy|da phx imp|db stp imp|dc jml absil|dd cmp absx|de dec absx|df cmp longx
e0 cpx immx|e1 sbc dpxi|e2 sep imm8|e3 sbc sr|e4 cpx dp|e5 sbc dp|e6 inc dp|e7 sbc dpil|e8 inx imp|e9 sbc immm|ea nop imp|eb xba imp|ec cpx abs|ed sbc abs|ee inc abs|ef sbc long
f0 beq rel|f1 sbc dpiy|f2 sbc dpi|f3 sbc sriy|f4 pea abs|f5 sbc dpx|f6 inc dpx|f7 sbc dpil|f8 sed imp|f9 sbc absy|fa plx imp|fb xce imp|fc jsr absxi|fd sbc absx|fe inc absx|ff sbc longx
"""
OPS = {}
for item in T.replace('\n', '|').split('|'):
    item = item.strip()
    if not item: continue
    o, m, md = item.split()
    OPS[int(o, 16)] = (m, md)
SZ = dict(imp=0, acc=0, imm8=1, dp=1, dpx=1, dpy=1, dpi=1, dpxi=1, dpiy=1, dpil=1, dpily=1, sr=1, sriy=1,
          rel=1, abs=2, absx=2, absy=2, absi=2, absxi=2, absil=2, rell=2, mv=2, long=3, longx=3)

class ROM:
    def __init__(s, path, labels=None):
        s.d = open(path, 'rb').read()
        s.labels = labels or {}
    def off(s, a):
        b = (a >> 16) & 0x7f; lo = a & 0xffff
        if lo < 0x8000: return None
        o = b * 0x8000 + (lo - 0x8000)
        return o if o < len(s.d) else None
    def rb(s, a):
        o = s.off(a); return None if o is None else s.d[o]
    def rw(s, a): return s.rb(a) | (s.rb(a + 1) << 8)
    def rl(s, a): return s.rw(a) | (s.rb(a + 2) << 16)

def decode(rom, a, m, x):
    op = rom.rb(a)
    mn, md = OPS[op]
    n = SZ.get(md)
    if md == 'immm': n = 1 if m else 2
    if md == 'immx': n = 1 if x else 2
    v = 0
    for i in range(n): v |= rom.rb(a + 1 + i) << (8 * i)
    bank = a & 0xff0000
    tgt = None
    if md == 'imp' or md == 'acc': s = '' if md == 'imp' else 'a'
    elif md in ('immm', 'immx', 'imm8'): s = f'#${v:0{n*2}x}'
    elif md == 'dp': s = f'${v:02x}'
    elif md == 'dpx': s = f'${v:02x},x'
    elif md == 'dpy': s = f'${v:02x},y'
    elif md == 'dpi': s = f'(${v:02x})'
    elif md == 'dpxi': s = f'(${v:02x},x)'
    elif md == 'dpiy': s = f'(${v:02x}),y'
    elif md == 'dpil': s = f'[${v:02x}]'
    elif md == 'dpily': s = f'[${v:02x}],y'
    elif md == 'sr': s = f'${v:02x},s'
    elif md == 'sriy': s = f'(${v:02x},s),y'
    elif md == 'rel':
        tgt = bank | ((a + 2 + ((v ^ 0x80) - 0x80)) & 0xffff); s = f'${tgt&0xffff:04x}'
    elif md == 'rell':
        tgt = bank | ((a + 3 + ((v ^ 0x8000) - 0x8000)) & 0xffff); s = f'${tgt&0xffff:04x}'
    elif md == 'abs':
        s = f'${v:04x}'
        if mn in ('jsr', 'jmp'): tgt = bank | v
    elif md == 'absx': s = f'${v:04x},x'
    elif md == 'absy': s = f'${v:04x},y'
    elif md == 'absi': s = f'(${v:04x})'
    elif md == 'absxi': s = f'(${v:04x},x)'
    elif md == 'absil': s = f'[${v:04x}]'
    elif md == 'mv': s = f'${v&0xff:02x},${v>>8:02x}'
    elif md == 'long':
        s = f'${v:06x}'
        if mn in ('jsl', 'jml'): tgt = v
    elif md == 'longx': s = f'${v:06x},x'
    return op, mn, md, n + 1, v, s, tgt

def trace(rom, entries, maxn=200000):
    """entries: list of (addr, m, x). returns dict addr->(m,x,len,text,tgt)"""
    code = {}
    q = collections.deque(entries)
    seen = set()
    while q:
        a, m, x = q.popleft()
        while True:
            if (a, m, x) in seen: break
            seen.add((a, m, x))
            if rom.off(a) is None: break
            op, mn, md, ln, v, s, tgt = decode(rom, a, m, x)
            code.setdefault(a, (m, x, ln, mn, s, tgt))
            nm, nx = m, x
            if mn == 'rep':
                if v & 0x20: nm = 0
                if v & 0x10: nx = 0
            if mn == 'sep':
                if v & 0x20: nm = 1
                if v & 0x10: nx = 1
            if mn in ('plp',):
                pass  # keep assumption
            if tgt is not None and mn not in ('per',):
                if mn in ('jsr', 'jsl'):
                    q.append((tgt, m, x))
                else:
                    q.append((tgt, nm, nx))
            if mn in ('rts', 'rtl', 'rti', 'jmp', 'jml', 'bra', 'brl', 'stp', 'brk'):
                break
            if mn in ('jsr', 'jsl') and tgt is not None and tgt in rom.labels.get('_noreturn', ()):
                break
            a = (a & 0xff0000) | ((a + ln) & 0xffff)
            m, x = nm, nx
    return code

def listing(rom, code, comments=None):
    out = []
    comments = comments or {}
    last = None
    for a in sorted(code):
        m, x, ln, mn, s, tgt = code[a]
        if last is not None and a != last: out.append('')
        raw = ' '.join('%02x' % rom.rb(a + i) for i in range(ln))
        lab = rom.labels.get(a)
        if lab: out.append(f'{lab}:')
        c = comments.get(a, '')
        out.append(f'{a>>16:02x}:{a&0xffff:04x} {"M" if m else "m"}{"X" if x else "x"} {raw:12s} {mn} {s}' + (f'   ; {c}' if c else ''))
        last = (a & 0xff0000) | ((a + ln) & 0xffff)
    return '\n'.join(out)

if __name__ == '__main__':
    rom = ROM(sys.argv[1])
    ents = []
    for e in sys.argv[2:]:
        p = e.split(':')
        ents.append((int(p[0], 16), int(p[1]) if len(p) > 1 else 1, int(p[2]) if len(p) > 2 else 1))
    code = trace(rom, ents)
    print(listing(rom, code))

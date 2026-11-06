"""Classify SNES WRAM ($7E:0000-$7F:FFFF) by how the SGB firmware uses it.
Input: ram/<fw>_<scenario>.bin (per-address stats from the instrumented bsnes) and .log (boot state per frame)."""
import struct, sys, os, re, glob, collections, json
REC = struct.Struct('<8I6I6I')          # rc wc rfirst rlast wfirst wlast rseg wseg rpc[6] wpc[6]
N = 0x20000
ATTR_OVR = {0xc1e0, 0xc1e6, 0xc1e3, 0xc1e9}   # recorded PCs of lda/sta [$a8],y in $C1xx (v1.1/1.2, v1.0)

def load(path):
    d = open(path, 'rb').read()
    assert len(d) == N * REC.size, path
    return d

def mainloop_start(logpath):
    """first frame where the boot state machine reached $0F/5 (main loop entered ~2 frames later)"""
    for l in open(logpath):
        m = re.search(r'end of F(\d+): state \$0100=0f \$0101=05', l)
        if m: return int(m.group(1)) + 2
    return None

def scan(fw, scen, exclude_pcs=()):
    """returns dict addr -> (boot_access, runtime_access, rpcs, wpcs)"""
    d = load(f'ram/{fw}_{scen}.bin'); ml = mainloop_start(f'ram/{fw}_{scen}.log')
    out = {}
    for a in range(N):
        rc, wc, rf, rl, wf, wl, rs, ws, *pcs = REC.unpack_from(d, a * REC.size)
        rpc = [p - 1 for p in pcs[:6] if p]; wpc = [p - 1 for p in pcs[6:] if p]
        # DATA_SND/DATA_TRN payload writes, test payload code, and (SGB1 only) the ATTR_BLK fill overrunning
        # past the attribute map because cmdtest.gb sent one malformed block (y1=27 > y2): not normal use
        isx = lambda p: p in exclude_pcs or (p >> 16 in (0, 0x7e) and 0x1A00 <= (p & 0xffff) <= 0x1AFF) or (a >= 0xB000 and a < 0x10000 and p in ATTR_OVR)
        if wc and all(isx(p) for p in wpc):
            wc = 0; wpc = []
        if rc and all(isx(p) for p in rpc):
            rc = 0; rpc = []
        if not rc and not wc: continue
        last = max(rl if rc else 0, wl if wc else 0)
        first = min(rf if rc else 1 << 30, wf if wc else 1 << 30)
        boot = ml is None or first < ml
        run = ml is not None and last >= ml
        out[a] = (boot, run, rpc, wpc)
    return out, ml

def ranges(addrs):
    addrs = sorted(addrs); res = []
    for a in addrs:
        if res and a == res[-1][1] + 1: res[-1][1] = a
        else: res.append([a, a])
    return res

def fmt(a): return f'${0x7e + (a >> 16):02X}:{a & 0xffff:04X}'

SCEN = ['idle', 'cmd', 'monkey', 'saver', 'credits', 'paint', 'borders', 'paintreset', 'reset', 'badlogo', 'borders012']

def payload_pcs(fw):
    d = load(f'ram/{fw}_cmd.bin'); pcs = set()
    for a in (0x1fff0, 0x1e000):
        *_, = REC.unpack_from(d, a * REC.size)
        rec = REC.unpack_from(d, a * REC.size)
        pcs |= {p - 1 for p in rec[14:20] if p}
    return pcs

def classify(fw):
    ex = payload_pcs(fw)
    S = {}
    for sc in SCEN:
        if os.path.exists(f'ram/{fw}_{sc}.bin'):
            S[sc] = scan(fw, sc, ex)
    cls = {}
    info = collections.defaultdict(lambda: {'scen': set(), 'wpc': set(), 'rpc': set()})
    for a in range(N):
        run_in = set(); boot_any = False; any_acc = False
        for sc, (m, ml) in S.items():
            if a in m:
                boot, run, rpc, wpc = m[a]; any_acc = True
                info[a]['wpc'] |= set(wpc); info[a]['rpc'] |= set(rpc)
                if sc in ('reset', 'badlogo', 'paintreset'):
                    info[a]['scen'].add(sc); continue
                if run: run_in.add(sc)
                if boot: boot_any = True
        if not any_acc: c = 'free'
        elif 'idle' in run_in: c = 'runtime'
        elif run_in: c = 'feature:' + '+'.join(sorted(run_in))
        elif boot_any: c = 'boot'
        else: c = 'special:' + '+'.join(sorted(info[a]['scen']))
        cls[a] = c
    return cls, info, ex

def summarize(fw, out):
    cls, info, ex = classify(fw)
    # compact into runs of equal class
    runs = []
    for a in range(N):
        c = cls[a]
        if runs and runs[-1][2] == c and runs[-1][1] == a - 1: runs[-1][1] = a
        else: runs.append([a, a, c])
    json.dump({'fw': fw, 'exclude_pcs': sorted(ex), 'runs': runs}, open(out, 'w'))
    return cls, info, runs

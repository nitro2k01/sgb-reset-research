import re,sys,difflib
R=re.compile(r'^(\S+) (\S\S) ((?:[0-9a-f]{2} )+)\s*(\w+) ?(.*)$')
def norm(f):
    out=[]
    for l in open(f):
        m=R.match(l.rstrip('\n'))
        if not m: continue
        mn,op=m.group(4),m.group(5).strip()
        if mn[0] in 'bj' and mn not in ('bit',): op=re.sub(r'\$[0-9a-f]{4,6}','$X',op)
        out.append((m.group(1),mn+' '+op))
    return out
a=norm(sys.argv[1]); b=norm(sys.argv[2])
sm=difflib.SequenceMatcher(None,[x[1] for x in a],[x[1] for x in b],autojunk=False)
for op,i1,i2,j1,j2 in sm.get_opcodes():
    if op!='equal':
        print('==',op, a[i1][0] if i1<len(a) else '', '->', b[j1][0] if j1<len(b) else '')
        for x in a[i1:i2][:40]: print('  -',x[0],x[1])
        for x in b[j1:j2][:40]: print('  +',x[0],x[1])

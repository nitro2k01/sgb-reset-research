# Collect WRAM addresses referenced by operands in a traced listing (approximation:
# abs operands < $2000 = low RAM via mirror; long operands in banks $7E/$7F; dp operands = $00xx (D=0)).
import re,sys,collections,json
R=re.compile(r'^(\S+) (\S\S) ((?:[0-9a-f]{2} )+)\s*(\w+) ?(.*)$')
refs=collections.defaultdict(set)
for l in open(sys.argv[1]):
    m=R.match(l.rstrip('\n'))
    if not m: continue
    pc,mn,op=m.group(1),m.group(4),m.group(5)
    if mn in ('jmp','jml','jsr','jsl','pea','per','mvn','mvp') or op.startswith('#'): continue
    if mn[0]=='b' and mn not in ('bit',): continue
    mm=re.match(r'[\[(]?\$([0-9a-f]+)',op)
    if not mm: continue
    v=int(mm.group(1),16); n=len(mm.group(1))
    if n==2: a=v                      # direct page (D=0)
    elif n==4: a=v if v<0x2000 else None
    else: a=(v-0x7e0000) if 0x7e0000<=v<=0x7fffff else (v&0xffff if (v>>16)&0x7f<0x40 and (v&0xffff)<0x2000 else None)
    if a is None: continue
    refs[a].add(pc+(' idx' if re.search(r',[xy]|\),y|\],y',op) else ''))
json.dump({hex(k):sorted(v) for k,v in refs.items()},open(sys.argv[2],'w'))
print(sys.argv[1],len(refs),'distinct WRAM operand addresses')

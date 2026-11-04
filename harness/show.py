import sys
f,s,e=sys.argv[1],int(sys.argv[2],16),int(sys.argv[3],16)
for l in open(f):
    try: a=int(l[:2],16)<<16|int(l[3:7],16)
    except: continue
    if s<=a<e: print(l,end='')

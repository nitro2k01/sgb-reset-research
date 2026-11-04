import subprocess
def run(h):
    rom=bytearray(32768); rom[0x104:0x150]=h; open('t.gb','wb').write(rom)
    o=subprocess.run(['./boottime','../w/boot.bin','t.gb','1'],capture_output=True,text=True).stdout.split('\n')[-2].split()
    return int(o[1])
pc=lambda b: sum(bin(x).count('1') for x in b)
def pk(h):
    P=[]
    for k,cmd in enumerate([0xf1,0xf3,0xf5,0xf7,0xf9,0xfb]):
        n=14 if k<5 else 6; d=h[14*k:14*k+n]; P.append(pc(bytes([cmd,sum(d)&0xff])+d))
    return P
base=bytearray(76)
for slot,off in ((6,0x14c-0x104),(5,0x13c-0x104),(4,0x134-0x104),(1,0x104-0x104)):
    res=[]
    for v in [0,1,3,7,0xf,0x1f,0x3f,0x7f,0xff]:
        h=bytearray(base); h[off]=v
        res.append((pk(h)[slot-1],run(bytes(h))))
    print('vary packet',slot,res)

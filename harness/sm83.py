import sys
r8=['b','c','d','e','h','l','(hl)','a']
r16=['bc','de','hl','sp']
r16s=['bc','de','hl','af']
cc=['nz','z','nc','c']
alu=['add a,','adc a,','sub ','sbc a,','and ','xor ','or ','cp ']
rot=['rlc','rrc','rl','rr','sla','sra','swap','srl']
def dis(b,pc,base=0):
    o=b[pc];n=lambda:b[pc+1];nn=lambda:b[pc+1]|(b[pc+2]<<8)
    x,y,z=o>>6,(o>>3)&7,o&7
    if o==0xcb:
        c=b[pc+1];x2,y2,z2=c>>6,(c>>3)&7,c&7
        if x2==0:return 2,f'{rot[y2]} {r8[z2]}'
        return 2,f"{['','bit','res','set'][x2]} {y2},{r8[z2]}"
    if x==1:
        if o==0x76:return 1,'halt'
        return 1,f'ld {r8[y]},{r8[z]}'
    if x==2:return 1,alu[y]+r8[z]
    if x==0:
        if z==0:
            if y==0:return 1,'nop'
            if y==1:return 3,f'ld (${nn():04x}),sp'
            if y==2:return 2,'stop'
            rel=lambda:(pc+2+((n()^0x80)-0x80)+base)&0xffff
            if y==3:return 2,f'jr ${rel():04x}'
            return 2,f'jr {cc[y-4]},${rel():04x}'
        if z==1:
            if y&1:return 1,f'add hl,{r16[y>>1]}'
            return 3,f'ld {r16[y>>1]},${nn():04x}'
        if z==2:
            t=['(bc)','(de)','(hl+)','(hl-)'][y>>1]
            return 1,(f'ld a,{t}' if y&1 else f'ld {t},a')
        if z==3:return 1,f"{'dec' if y&1 else 'inc'} {r16[y>>1]}"
        if z==4:return 1,f'inc {r8[y]}'
        if z==5:return 1,f'dec {r8[y]}'
        if z==6:return 2,f'ld {r8[y]},${n():02x}'
        return 1,['rlca','rrca','rla','rra','daa','cpl','scf','ccf'][y]
    # x==3
    if z==0:
        if y<4:return 1,f'ret {cc[y]}'
        return 2,[f'ldh ($ff{n():02x}),a',f'add sp,{n()}',f'ldh a,($ff{n():02x})',f'ld hl,sp+{n()}'][y-4]
    if z==1:
        if y&1==0:return 1,f'pop {r16s[y>>1]}'
        return 1,['ret','reti','jp hl','ld sp,hl'][y>>1]
    if z==2:
        if y<4:return 3,f'jp {cc[y]},${nn():04x}'
        return [(1,'ld ($ff00+c),a'),(3,f'ld (${nn():04x}),a'),(1,'ld a,($ff00+c)'),(3,f'ld a,(${nn():04x})')][y-4]
    if z==3:
        if y==0:return 3,f'jp ${nn():04x}'
        if y==6:return 1,'di'
        if y==7:return 1,'ei'
        return 1,f'db ${o:02x}'
    if z==4:
        if y<4:return 3,f'call {cc[y]},${nn():04x}'
        return 1,f'db ${o:02x}'
    if z==5:
        if y&1==0:return 1,f'push {r16s[y>>1]}'
        if y==1:return 3,f'call ${nn():04x}'
        return 1,f'db ${o:02x}'
    if z==6:return 2,alu[y]+f'${n():02x}'
    return 1,f'rst ${y*8:02x}'
if __name__=='__main__':
    b=open(sys.argv[1],'rb').read()+b'\0\0\0'
    s=int(sys.argv[2],16) if len(sys.argv)>2 else 0
    e=int(sys.argv[3],16) if len(sys.argv)>3 else len(b)-3
    pc=s
    while pc<e:
        l,t=dis(b,pc)
        print(f'{pc:04x}: {" ".join("%02x"%x for x in b[pc:pc+l]):10s} {t}')
        pc+=l

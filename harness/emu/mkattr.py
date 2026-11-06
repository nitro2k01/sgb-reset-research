import mkscript
P=lambda *b: ('pkt',bytes(b)); W=lambda n: ('wait',n)
T={
 'blk1':[P(0x21,1, 0x07,0x12, 2,2,10,10)],
 'blk2':[P(0x22,3, 0x07,0x00,0,0,19,17, 0x03,0x05,1,1,5,5, 0x07), P(0,0x1b,3,3,8,8,0,0,0,0,0,0,0,0,0,0)],
 'lin':[P(0x29,3, 0x85,0xa3,0x42)],
 'div1':[P(0x31,0x5b,9)],
 'div2':[P(0x31,0x24,4)],
 'chr':[P(0x39,2,3,10,0,0, 0x1b,0xe4,0x55)],
}
for k,v in T.items():
    mkscript.build(f'attr_{k}.gb',[W(90)]+[x for p in v for x in (p,W(6))],[])

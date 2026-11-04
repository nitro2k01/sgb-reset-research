import sys
d=open(sys.argv[1],'rb').read()
pat=bytes.fromhex(sys.argv[2])
i=d.find(pat)
while i>=0:
    o=i
    print(f'{o//0x8000:02x}:{0x8000+o%0x8000:04x}', d[max(0,o-2):o+len(pat)+2].hex())
    i=d.find(pat,i+1)

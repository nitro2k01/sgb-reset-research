import zlib,struct,sys
for fn in sys.argv[1:]:
    d=open(fn,'rb').read(); hdr,rest=d.split(b'\n',1); _,w,h,_=hdr.split(); w=int(w);h=int(h)
    raw=b''.join(b'\0'+rest[y*w*3:(y+1)*w*3] for y in range(h))
    def ch(t,b): return struct.pack('>I',len(b))+t+b+struct.pack('>I',zlib.crc32(t+b)&0xffffffff)
    open(fn.replace('.ppm','.png'),'wb').write(b'\x89PNG\r\n\x1a\n'+ch(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+ch(b'IDAT',zlib.compress(raw))+ch(b'IEND',b''))

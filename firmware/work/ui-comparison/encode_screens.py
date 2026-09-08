from pathlib import Path
import zlib,struct
root=Path(__file__).parent/'screens'
def png(path,w,h,rgb):
 def chunk(tag,data): return struct.pack('!I',len(data))+tag+data+struct.pack('!I',zlib.crc32(tag+data)&0xffffffff)
 raw=b''.join(b'\0'+rgb[y*w*3:(y+1)*w*3] for y in range(h))
 path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw,9))+chunk(b'IEND',b''))
for f in root.glob('*.ppm'):
 png(f.with_suffix('.png'),480,320,f.read_bytes().split(b'\n',3)[3])
 f.unlink()
print(sum(f.stat().st_size for f in root.glob('*.png')), 'PNG bytes')

import struct, sys

# 把 __versions 段改名（同名长度），让内核 find_sec("__versions") 找不到 → versindex=0
src, dst = sys.argv[1], sys.argv[2]
d = bytearray(open(src, 'rb').read())
e_shoff = struct.unpack_from('<Q', d, 0x28)[0]
e_shentsize = struct.unpack_from('<H', d, 0x3a)[0]
e_shnum = struct.unpack_from('<H', d, 0x3c)[0]
e_shstrndx = struct.unpack_from('<H', d, 0x3e)[0]
o = e_shoff + e_shstrndx * e_shentsize
stroff = struct.unpack_from('<Q', d, o + 24)[0]
stsize = struct.unpack_from('<Q', d, o + 32)[0]
strtab = bytes(d[stroff:stroff + stsize])
idx = strtab.find(b'__versions\x00')
if idx < 0:
    print('no __versions'); sys.exit(1)
# 找到指向该名字的段
hit = None
for i in range(e_shnum):
    o = e_shoff + i * e_shentsize
    nameoff = struct.unpack_from('<I', d, o)[0]
    if nameoff == idx:
        hit = i
        break
if hit is None:
    print('section not found'); sys.exit(1)
o = e_shoff + hit * e_shentsize
sh_size = struct.unpack_from('<Q', d, o + 32)[0]
print(f'section #{hit} __versions size={sh_size}')
# 名字改成同长度：__versionz
d[stroff + idx:stroff + idx + 10] = b'__versionz'
# 段类型清成 SHT_NULL，大小清零 → 内核完全看不到
struct.pack_into('<I', d, o + 4, 0)
struct.pack_into('<Q', d, o + 32, 0)
open(dst, 'wb').write(d)
print('patched ->', dst)

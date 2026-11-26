import struct, sys

p = sys.argv[1]
d = open(p, 'rb').read()
e_shoff = struct.unpack_from('<Q', d, 0x28)[0]
e_shentsize = struct.unpack_from('<H', d, 0x3a)[0]
e_shnum = struct.unpack_from('<H', d, 0x3c)[0]
e_shstrndx = struct.unpack_from('<H', d, 0x3e)[0]

secs = []
for i in range(e_shnum):
    o = e_shoff + i * e_shentsize
    name, typ, flags, addr, off, size, link, info, align, entsize = struct.unpack_from('<IIQQQQIIQQ', d, o)
    secs.append(dict(name=name, typ=typ, off=off, size=size, link=link, entsize=entsize, i=i))

strtab = d[secs[e_shstrndx]['off']:secs[e_shstrndx]['off'] + secs[e_shstrndx]['size']]
for s in secs:
    s['nm'] = strtab[s['name']:strtab.index(b'\0', s['name'])].decode('utf-8', 'replace')

sym = [s for s in secs if s['nm'] == '.symtab'][0]
strs = [s for s in secs if s['i'] == sym['link']][0]
stab = d[strs['off']:strs['off'] + strs['size']]

print("undefined (imported) symbols:")
imported = []
for i in range(0, sym['size'], sym['entsize']):
    st_name, st_info, st_other, st_shndx, st_value, st_size = struct.unpack_from('<IBBHQQ', d, sym['off'] + i)
    if st_shndx == 0 and st_name:
        nm = stab[st_name:stab.index(b'\0', st_name)].decode('utf-8', 'replace')
        imported.append(nm)
        print("  ", nm)
print("\ncount:", len(imported))

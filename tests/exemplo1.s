    .section .data
a:    .long 0   # variável/temporário
b:    .long 0   # variável/temporário
i:    .long 0   # variável/temporário
n:    .long 0   # variável/temporário
t0:    .long 0   # variável/temporário
t1:    .long 0   # variável/temporário
t2:    .long 0   # variável/temporário
temp:    .long 0   # variável/temporário

    .section .text
    .globl main
main:
    pushq %rbp
    movq %rsp, %rbp
    # TAC:   n = 10
    movl $10, %eax
    movl %eax, n(%rip)
    # TAC:   a = 0
    movl $0, %eax
    movl %eax, a(%rip)
    # TAC:   b = 1
    movl $1, %eax
    movl %eax, b(%rip)
    # TAC:   i = 0
    movl $0, %eax
    movl %eax, i(%rip)
    # TAC:   print a
    movl a(%rip), %esi
    leaq fmt_int(%rip), %rdi
    xorl %eax, %eax
    call printf
L0:
    # TAC:   t0 = i < n
    movl i(%rip), %eax
    movl n(%rip), %ebx
    cmpl %ebx, %eax
    setl %al
    movzbl %al, %eax
    movl %eax, t0(%rip)
    # TAC:   if_false t0 goto L1
    movl t0(%rip), %eax
    testl %eax, %eax
    je L1
    # TAC:   t1 = a + b
    movl a(%rip), %eax
    movl b(%rip), %ebx
    addl %ebx, %eax
    movl %eax, t1(%rip)
    # TAC:   temp = t1
    movl t1(%rip), %eax
    movl %eax, temp(%rip)
    # TAC:   a = b
    movl b(%rip), %eax
    movl %eax, a(%rip)
    # TAC:   b = temp
    movl temp(%rip), %eax
    movl %eax, b(%rip)
    # TAC:   print a
    movl a(%rip), %esi
    leaq fmt_int(%rip), %rdi
    xorl %eax, %eax
    call printf
    # TAC:   t2 = i + 1
    movl i(%rip), %eax
    movl $1, %ebx
    addl %ebx, %eax
    movl %eax, t2(%rip)
    # TAC:   i = t2
    movl t2(%rip), %eax
    movl %eax, i(%rip)
    # TAC:   goto L0
    jmp L0
L1:
    xorl %eax, %eax
    popq %rbp
    ret

    .section .rodata
fmt_int: .string "%d\n"
fmt_str: .string "%s\n"
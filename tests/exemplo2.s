    .section .data
a:    .long 0   # variável/temporário
b:    .long 0   # variável/temporário
c:    .long 0   # variável/temporário
resultado:    .long 0   # variável/temporário
t0:    .long 0   # variável/temporário
t1:    .long 0   # variável/temporário
t2:    .long 0   # variável/temporário
t3:    .long 0   # variável/temporário
t4:    .long 0   # variável/temporário
x:    .long 0   # variável/temporário
y:    .long 0   # variável/temporário
z:    .long 0   # variável/temporário

    .section .text
    .globl main
main:
    pushq %rbp
    movq %rsp, %rbp
    # TAC:   x = 42
    movl $42, %eax
    movl %eax, x(%rip)
    # TAC:   y = 17
    movl $17, %eax
    movl %eax, y(%rip)
    # TAC:   t0 = x > y
    movl x(%rip), %eax
    movl y(%rip), %ebx
    cmpl %ebx, %eax
    setg %al
    movzbl %al, %eax
    movl %eax, t0(%rip)
    # TAC:   resultado = t0
    movl t0(%rip), %eax
    movl %eax, resultado(%rip)
    # TAC:   if_false resultado goto L0
    movl resultado(%rip), %eax
    testl %eax, %eax
    je L0
    # TAC:   print x
    movl x(%rip), %esi
    leaq fmt_int(%rip), %rdi
    xorl %eax, %eax
    call printf
    # TAC:   goto L1
    jmp L1
L0:
    # TAC:   print y
    movl y(%rip), %esi
    leaq fmt_int(%rip), %rdi
    xorl %eax, %eax
    call printf
L1:
    # TAC:   t1 = x + y
    movl x(%rip), %eax
    movl y(%rip), %ebx
    addl %ebx, %eax
    movl %eax, t1(%rip)
    # TAC:   t2 = t1 * 2
    movl t1(%rip), %eax
    movl $2, %ebx
    imull %ebx, %eax
    movl %eax, t2(%rip)
    # TAC:   z = t2
    movl t2(%rip), %eax
    movl %eax, z(%rip)
    # TAC:   print z
    movl z(%rip), %esi
    leaq fmt_int(%rip), %rdi
    xorl %eax, %eax
    call printf
    # TAC:   a = True
    movl $1, %eax
    movl %eax, a(%rip)
    # TAC:   b = False
    movl $0, %eax
    movl %eax, b(%rip)
    # TAC:   t3 = !b
    movl b(%rip), %eax
    testl %eax, %eax
    sete %al
    movzbl %al, %eax
    movl %eax, t3(%rip)
    # TAC:   t4 = a && t3
    movl a(%rip), %eax
    movl t3(%rip), %ebx
    andl %ebx, %eax
    movl %eax, t4(%rip)
    # TAC:   c = t4
    movl t4(%rip), %eax
    movl %eax, c(%rip)
    # TAC:   print c
    movl c(%rip), %esi
    leaq fmt_int(%rip), %rdi
    xorl %eax, %eax
    call printf
    xorl %eax, %eax
    popq %rbp
    ret

    .section .rodata
fmt_int: .string "%d\n"
fmt_str: .string "%s\n"
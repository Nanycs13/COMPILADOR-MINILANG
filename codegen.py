"""
=============================================================================
GERAÇÃO DE CÓDIGO FINAL — Compilador MiniLang
=============================================================================
Duas saídas disponíveis:

1. Interpretador de TAC — executa o código intermediário diretamente
   (útil para teste e validação da IR sem depender de assembler externo)

2. Gerador de Assembly x86 (sintaxe AT&T / GAS)
   Traduz cada instrução TAC para sequência de instruções x86 equivalentes.
   Variáveis e temporários → endereços em memória (seção .data / pilha).
=============================================================================
"""

from typing import List, Dict, Optional
from ir_generator import TACInstr


# ---------------------------------------------------------------------------
# Interpretador de TAC (execução direta para validação)
# ---------------------------------------------------------------------------
class TACInterpreter:
    """
    Executa as instruções TAC em uma máquina virtual simples.
    Útil para verificar a corretude do compilador sem gerar código nativo.
    """

    def __init__(self, instructions: List[TACInstr]):
        self.instructions = instructions
        self.memory: Dict[str, object] = {}   # variáveis e temporários
        # Mapa de rótulos → índice de instrução
        self.labels: Dict[str, int] = {
            instr.result: i
            for i, instr in enumerate(instructions)
            if instr.op == 'label'
        }
        self.output: List[str] = []

    def _resolve(self, operand) -> object:
        """Resolve um operando: constante direta ou variável."""
        if isinstance(operand, (int, bool)):
            return operand
        if isinstance(operand, str):
            if operand.startswith('"') and operand.endswith('"'):
                return operand[1:-1]   # string literal
            return self.memory.get(operand, 0)
        return operand

    def run(self, inputs: Optional[List[int]] = None) -> List[str]:
        """Executa o programa TAC. inputs: valores para instrução 'read'."""
        inputs = list(inputs or [])
        pc = 0
        max_steps = 100_000   # proteção contra loop infinito

        for _ in range(max_steps):
            if pc >= len(self.instructions):
                break
            instr = self.instructions[pc]
            pc += 1

            op = instr.op
            if op == 'label':
                continue

            if op == 'copy':
                self.memory[instr.result] = self._resolve(instr.arg1)

            elif op == 'print':
                val = self._resolve(instr.arg1)
                self.output.append(str(val))

            elif op == 'read':
                val = int(inputs.pop(0)) if inputs else int(input(f"read({instr.result}): "))
                self.memory[instr.result] = val

            elif op == 'goto':
                pc = self.labels[instr.arg1] + 1

            elif op == 'if_false':
                cond = self._resolve(instr.arg1)
                if not cond:
                    pc = self.labels[instr.arg2] + 1

            elif op == 'unary_minus':
                self.memory[instr.result] = -self._resolve(instr.arg1)

            elif op == 'unary_not':
                self.memory[instr.result] = not self._resolve(instr.arg1)

            else:
                # Operadores binários
                a = self._resolve(instr.arg1)
                b = self._resolve(instr.arg2)
                ops = {
                    '+': lambda x,y: x + y,
                    '-': lambda x,y: x - y,
                    '*': lambda x,y: x * y,
                    '/': lambda x,y: x // y,
                    '==': lambda x,y: x == y,
                    '!=': lambda x,y: x != y,
                    '<':  lambda x,y: x < y,
                    '>':  lambda x,y: x > y,
                    '<=': lambda x,y: x <= y,
                    '>=': lambda x,y: x >= y,
                    '&&': lambda x,y: bool(x) and bool(y),
                    '||': lambda x,y: bool(x) or bool(y),
                }
                if op in ops:
                    self.memory[instr.result] = ops[op](a, b)

        return self.output


# ---------------------------------------------------------------------------
# Gerador de Assembly x86 (AT&T syntax)
# ---------------------------------------------------------------------------
class X86Generator:
    """
    Traduz instruções TAC para Assembly x86 (AT&T, GAS).
    Todas as variáveis são alocadas na seção .data (inteiros de 32 bits).
    Usa %eax e %ebx como registradores de trabalho.

    Para compilar o .s gerado (Linux):
      gcc -m32 -o programa output.s
    """

    def __init__(self, instructions: List[TACInstr]):
        self.instructions = instructions
        # Coleta todos os nomes de variáveis e temporários
        self.vars = self._collect_vars()

    def _collect_vars(self):
        names = set()
        for instr in self.instructions:
            for attr in (instr.result, instr.arg1, instr.arg2):
                if isinstance(attr, str) and not attr.startswith('L') \
                        and attr not in ('print', 'read', 'goto', 'label', 'if_false'):
                    names.add(attr)
        return names

    def _asm_val(self, operand) -> str:
        """Traduz operando TAC para sintaxe AT&T."""
        if isinstance(operand, bool):
            return f"${1 if operand else 0}"
        if isinstance(operand, int):
            return f"${operand}"
        if isinstance(operand, str):
            if operand.startswith('"'):
                return operand   # strings são tratadas separadamente
            return f"{operand}(%rip)"   # variável global (64-bit)
        return str(operand)

    def generate(self) -> str:
        lines = []

        # ── Seção de dados: declara todas as variáveis como int32 = 0
        lines.append("    .section .data")
        for var in sorted(self.vars):
            if not var.startswith('"'):
                lines.append(f"{var}:    .long 0   # variável/temporário")

        # ── Seção de texto
        lines.append("")
        lines.append("    .section .text")
        lines.append("    .globl main")
        lines.append("main:")
        lines.append("    pushq %rbp")
        lines.append("    movq %rsp, %rbp")

        # ── Traduz cada instrução TAC
        for instr in self.instructions:
            op = instr.op

            if op == 'label':
                lines.append(f"{instr.result}:")
                continue

            lines.append(f"    # TAC: {instr}")

            if op == 'copy':
                lines.append(f"    movl {self._asm_val(instr.arg1)}, %eax")
                lines.append(f"    movl %eax, {instr.result}(%rip)")

            elif op == 'print':
                # Chama printf via syscall (simplificado: usa write via syscall)
                lines.append(f"    movl {self._asm_val(instr.arg1)}, %esi")
                lines.append(f"    leaq fmt_int(%rip), %rdi")
                lines.append(f"    xorl %eax, %eax")
                lines.append(f"    call printf")

            elif op == 'read':
                lines.append(f"    leaq fmt_int(%rip), %rdi")
                lines.append(f"    leaq {instr.result}(%rip), %rsi")
                lines.append(f"    xorl %eax, %eax")
                lines.append(f"    call scanf")

            elif op == 'goto':
                lines.append(f"    jmp {instr.arg1}")

            elif op == 'if_false':
                lines.append(f"    movl {self._asm_val(instr.arg1)}, %eax")
                lines.append(f"    testl %eax, %eax")
                lines.append(f"    je {instr.arg2}")

            elif op == 'unary_minus':
                lines.append(f"    movl {self._asm_val(instr.arg1)}, %eax")
                lines.append(f"    negl %eax")
                lines.append(f"    movl %eax, {instr.result}(%rip)")

            elif op == 'unary_not':
                lines.append(f"    movl {self._asm_val(instr.arg1)}, %eax")
                lines.append(f"    testl %eax, %eax")
                lines.append(f"    sete %al")
                lines.append(f"    movzbl %al, %eax")
                lines.append(f"    movl %eax, {instr.result}(%rip)")

            elif op in ('+', '-', '*', '/'):
                lines.append(f"    movl {self._asm_val(instr.arg1)}, %eax")
                lines.append(f"    movl {self._asm_val(instr.arg2)}, %ebx")
                if op == '+': lines.append("    addl %ebx, %eax")
                elif op == '-': lines.append("    subl %ebx, %eax")
                elif op == '*': lines.append("    imull %ebx, %eax")
                elif op == '/':
                    lines.append("    cdq")
                    lines.append("    idivl %ebx")
                lines.append(f"    movl %eax, {instr.result}(%rip)")

            elif op in ('==', '!=', '<', '>', '<=', '>='):
                cmp_map = {'==': 'sete', '!=': 'setne', '<': 'setl',
                           '>': 'setg', '<=': 'setle', '>=': 'setge'}
                lines.append(f"    movl {self._asm_val(instr.arg1)}, %eax")
                lines.append(f"    movl {self._asm_val(instr.arg2)}, %ebx")
                lines.append(f"    cmpl %ebx, %eax")
                lines.append(f"    {cmp_map[op]} %al")
                lines.append(f"    movzbl %al, %eax")
                lines.append(f"    movl %eax, {instr.result}(%rip)")

            elif op in ('&&', '||'):
                lines.append(f"    movl {self._asm_val(instr.arg1)}, %eax")
                lines.append(f"    movl {self._asm_val(instr.arg2)}, %ebx")
                if op == '&&': lines.append("    andl %ebx, %eax")
                else:          lines.append("    orl  %ebx, %eax")
                lines.append(f"    movl %eax, {instr.result}(%rip)")

        # ── Epílogo
        lines.append("    xorl %eax, %eax")
        lines.append("    popq %rbp")
        lines.append("    ret")
        lines.append("")
        lines.append("    .section .rodata")
        lines.append('fmt_int: .string "%d\\n"')
        lines.append('fmt_str: .string "%s\\n"')

        return "\n".join(lines)

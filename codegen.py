

from ir_generator import TACInstr


class DictManual:

    def __init__(self):
        self._pares = []

    def set(self, chave, valor):
        for par in self._pares:
            if par[0] == chave:
                par[1] = valor
                return
        self._pares.append([chave, valor])

    def get(self, chave, padrao=0):
        for par in self._pares:
            if par[0] == chave:
                return par[1]
        return padrao

    def contem(self, chave):
        for par in self._pares:
            if par[0] == chave:
                return True
        return False

    def chaves(self):
        resultado = []
        for par in self._pares:
            resultado.append(par[0])
        return resultado

class TACInterpreter:

    def __init__(self, instrucoes):
        self.instrucoes = instrucoes
        self.memoria    = DictManual()
        self.saida      = []   

        self.rotulos = DictManual()
        for i in range(len(instrucoes)):
            instr = instrucoes[i]
            if instr.op == 'label':
                self.rotulos.set(instr.result, i)

    def _resolver(self, operando):
        if isinstance(operando, int) or isinstance(operando, bool):
            return operando
        if isinstance(operando, str):
            if len(operando) >= 2 and operando[0] == '"' and operando[len(operando)-1] == '"':
                # Remove as aspas manualmente
                return operando[1:len(operando)-1]
            return self.memoria.get(operando, 0)
        return operando

    def executar(self, entradas=None):
        if entradas is None:
            entradas = []
        # Copia para não modificar o original
        fila_entrada = []
        for v in entradas:
            fila_entrada.append(v)

        pc        = 0
        max_steps = 100000   

        passo = 0
        while passo < max_steps:
            if pc >= len(self.instrucoes):
                break

            instr = self.instrucoes[pc]
            pc   += 1
            passo += 1
            op    = instr.op

            if op == 'label':
                continue

            elif op == 'copy':
                self.memoria.set(instr.result, self._resolver(instr.arg1))

            elif op == 'print':
                val = self._resolver(instr.arg1)
                self.saida.append(str(val))

            elif op == 'read':
                if len(fila_entrada) > 0:
                    val = fila_entrada[0]
                    fila_entrada = fila_entrada[1:]
                else:
                    val = int(input("read(%s): " % instr.result))
                self.memoria.set(instr.result, val)

            elif op == 'goto':
                idx = self.rotulos.get(instr.arg1, -1)
                if idx >= 0:
                    pc = idx + 1

            elif op == 'if_false':
                cond = self._resolver(instr.arg1)
                if not cond:
                    idx = self.rotulos.get(instr.arg2, -1)
                    if idx >= 0:
                        pc = idx + 1

            elif op == 'unary_minus':
                self.memoria.set(instr.result, -self._resolver(instr.arg1))

            elif op == 'unary_not':
                val = self._resolver(instr.arg1)
                self.memoria.set(instr.result, not val)

            else:
                a = self._resolver(instr.arg1)
                b = self._resolver(instr.arg2)
                r = 0

                if   op == '+':  r = a + b
                elif op == '-':  r = a - b
                elif op == '*':  r = a * b
                elif op == '/':
                    
                    if b == 0:
                        r = 0   
                    else:
                        
                        neg = (a < 0) != (b < 0)
                        a_abs = a if a >= 0 else -a
                        b_abs = b if b >= 0 else -b
                        q = 0
                        while (q + 1) * b_abs <= a_abs:
                            q += 1
                        r = -q if neg else q
                elif op == '==': r = (a == b)
                elif op == '!=': r = (a != b)
                elif op == '<':  r = (a < b)
                elif op == '>':  r = (a > b)
                elif op == '<=': r = (a <= b)
                elif op == '>=': r = (a >= b)
                elif op == '&&': r = bool(a) and bool(b)
                elif op == '||': r = bool(a) or bool(b)

                self.memoria.set(instr.result, r)

        return self.saida


class X86Generator:


    def __init__(self, instrucoes):
        self.instrucoes = instrucoes
        self.variaveis  = self._coletar_variaveis()

    def _eh_nome_variavel(self, v):

        if v is None:
            return False
        if isinstance(v, int) or isinstance(v, bool):
            return False
        if isinstance(v, str):
            if v[0] == '"':
                return False   # string literal
            if len(v) > 0 and v[0] == 'L' and v[1:].isdigit():
                return False   # rótulo
            return True
        return False

    def _coletar_variaveis(self):
    
        vistos  = []
        nomes   = []

        for instr in self.instrucoes:
            for v in (instr.result, instr.arg1, instr.arg2):
                if self._eh_nome_variavel(v):
                    ja_existe = False
                    for visto in vistos:
                        if visto == v:
                            ja_existe = True
                            break
                    if not ja_existe:
                        vistos.append(v)
                        nomes.append(v)

        n = len(nomes)
        for i in range(n):
            for j in range(0, n - i - 1):
                if nomes[j] > nomes[j + 1]:
                    nomes[j], nomes[j + 1] = nomes[j + 1], nomes[j]

        return nomes

    def _operando_asm(self, v):
        if isinstance(v, bool):
            return "$%d" % (1 if v else 0)
        if isinstance(v, int):
            return "$%d" % v
        if isinstance(v, str):
            return "%s(%%rip)" % v   

        return str(v)

    def gerar(self):

        linhas = []

        linhas.append("    .section .data")
        for var in self.variaveis:
            linhas.append("%-12s .long 0" % (var + ":"))

        linhas.append("")
        linhas.append("    .section .text")
        linhas.append("    .globl main")
        linhas.append("main:")
        linhas.append("    pushq %rbp")
        linhas.append("    movq  %rsp, %rbp")

        for instr in self.instrucoes:
            op = instr.op

            if op == 'label':
                linhas.append("%s:" % instr.result)
                continue

            # Comentário mostrando a instrução TAC original
            linhas.append("    # %s" % str(instr))

            if op == 'copy':
                linhas.append("    movl %s, %%eax" % self._operando_asm(instr.arg1))
                linhas.append("    movl %%eax, %s(%s)" % (instr.result, "%rip"))

            elif op == 'print':
                linhas.append("    movl %s, %%esi" % self._operando_asm(instr.arg1))
                linhas.append("    leaq fmt_int(%rip), %rdi")
                linhas.append("    xorl %eax, %eax")
                linhas.append("    call printf")

            elif op == 'read':
                linhas.append("    leaq fmt_int(%rip), %rdi")
                linhas.append("    leaq %s(%%rip), %%rsi" % instr.result)
                linhas.append("    xorl %eax, %eax")
                linhas.append("    call scanf")

            elif op == 'goto':
                linhas.append("    jmp %s" % instr.arg1)

            elif op == 'if_false':
                linhas.append("    movl %s, %%eax" % self._operando_asm(instr.arg1))
                linhas.append("    testl %eax, %eax")
                linhas.append("    je %s" % instr.arg2)

            elif op == 'unary_minus':
                linhas.append("    movl %s, %%eax" % self._operando_asm(instr.arg1))
                linhas.append("    negl %eax")
                linhas.append("    movl %%eax, %s(%s)" % (instr.result, "%rip"))

            elif op == 'unary_not':
                linhas.append("    movl %s, %%eax" % self._operando_asm(instr.arg1))
                linhas.append("    testl %eax, %eax")
                linhas.append("    sete %al")
                linhas.append("    movzbl %al, %eax")
                linhas.append("    movl %%eax, %s(%s)" % (instr.result, "%rip"))

            elif op in ('+', '-', '*', '/'):
                linhas.append("    movl %s, %%eax" % self._operando_asm(instr.arg1))
                linhas.append("    movl %s, %%ebx" % self._operando_asm(instr.arg2))
                if   op == '+': linhas.append("    addl %ebx, %eax")
                elif op == '-': linhas.append("    subl %ebx, %eax")
                elif op == '*': linhas.append("    imull %ebx, %eax")
                elif op == '/':
                    linhas.append("    cdq")
                    linhas.append("    idivl %ebx")
                linhas.append("    movl %%eax, %s(%s)" % (instr.result, "%rip"))

            elif op in ('==', '!=', '<', '>', '<=', '>='):
                mapa = {'==': 'sete', '!=': 'setne', '<': 'setl',
                        '>': 'setg', '<=': 'setle', '>=': 'setge'}
                linhas.append("    movl %s, %%eax" % self._operando_asm(instr.arg1))
                linhas.append("    movl %s, %%ebx" % self._operando_asm(instr.arg2))
                linhas.append("    cmpl %ebx, %eax")
                linhas.append("    %s %%al" % mapa[op])
                linhas.append("    movzbl %al, %eax")
                linhas.append("    movl %%eax, %s(%s)" % (instr.result, "%rip"))

            elif op in ('&&', '||'):
                linhas.append("    movl %s, %%eax" % self._operando_asm(instr.arg1))
                linhas.append("    movl %s, %%ebx" % self._operando_asm(instr.arg2))
                if op == '&&': linhas.append("    andl %ebx, %eax")
                else:          linhas.append("    orl  %ebx, %eax")
                linhas.append("    movl %%eax, %s(%s)" % (instr.result, "%rip"))

        
        linhas.append("    xorl %eax, %eax")
        linhas.append("    popq %rbp")
        linhas.append("    ret")
        linhas.append("")
        linhas.append("    .section .rodata")
        linhas.append('fmt_int: .string "%d\\n"')
        linhas.append('fmt_str: .string "%s\\n"')

        
        resultado = ""
        for i in range(len(linhas)):
            if i == 0:
                resultado = linhas[0]
            else:
                resultado = resultado + "\n" + linhas[i]
        return resultado

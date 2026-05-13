"""
=============================================================================
GERAÇÃO DE CÓDIGO INTERMEDIÁRIO — Compilador MiniLang
=============================================================================
Representa o código fonte em Código de Três Endereços (TAC / Three-Address Code).

Formato geral de uma instrução TAC:
  result = op1  operator  op2      (atribuição binária)
  result = op   operand             (atribuição unária)
  result = value                    (cópia simples)
  label:                            (rótulo de salto)
  goto label                        (salto incondicional)
  if_false cond goto label          (salto condicional)
  param value                       (passa parâmetro)
  print value                       (saída)
  read result                       (entrada)

Temporários são gerados como t0, t1, t2, …
Rótulos são gerados como L0, L1, L2, …
=============================================================================
"""

from dataclasses import dataclass, field
from typing import List, Optional, Union
from ast_nodes import *


# ---------------------------------------------------------------------------
# Operandos TAC: constante inteira, booleana, string ou nome de variável/temp
# ---------------------------------------------------------------------------
Operand = Union[int, bool, str]   # int/bool = literal; str = nome


# ---------------------------------------------------------------------------
# Instrução TAC
# ---------------------------------------------------------------------------
@dataclass
class TACInstr:
    op:     str                   # operador ou instrução
    result: Optional[str] = None  # destino (temp ou variável)
    arg1:   Optional[Operand] = None
    arg2:   Optional[Operand] = None

    def __str__(self) -> str:
        # Formata a instrução para exibição legível
        if self.op == 'label':
            return f"{self.result}:"
        if self.op == 'goto':
            return f"  goto {self.arg1}"
        if self.op == 'if_false':
            return f"  if_false {self.arg1} goto {self.arg2}"
        if self.op == 'print':
            return f"  print {self.arg1}"
        if self.op == 'read':
            return f"  read {self.result}"
        if self.op == 'copy':
            return f"  {self.result} = {self.arg1}"
        if self.op in ('+', '-', '*', '/', '==', '!=', '<', '>', '<=', '>=', '&&', '||'):
            return f"  {self.result} = {self.arg1} {self.op} {self.arg2}"
        if self.op == 'unary_minus':
            return f"  {self.result} = -{self.arg1}"
        if self.op == 'unary_not':
            return f"  {self.result} = !{self.arg1}"
        return f"  {self.op} {self.result} {self.arg1} {self.arg2}"


# ---------------------------------------------------------------------------
# Gerador de código intermediário
# ---------------------------------------------------------------------------
class IRGenerator(Visitor):
    """
    Percorre a AST e emite instruções TAC.
    Implementa o Visitor Pattern para cada nó da AST.
    """

    def __init__(self):
        self.instructions: List[TACInstr] = []
        self._temp_count  = 0
        self._label_count = 0

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------
    def _new_temp(self) -> str:
        """Gera um novo temporário: t0, t1, t2, …"""
        t = f"t{self._temp_count}"
        self._temp_count += 1
        return t

    def _new_label(self) -> str:
        """Gera um novo rótulo: L0, L1, L2, …"""
        l = f"L{self._label_count}"
        self._label_count += 1
        return l

    def _emit(self, instr: TACInstr):
        self.instructions.append(instr)

    def generate(self, tree: Program) -> List[TACInstr]:
        tree.accept(self)
        return self.instructions

    def code_str(self) -> str:
        return "\n".join(str(i) for i in self.instructions)

    # -----------------------------------------------------------------------
    # Visitores de instruções
    # -----------------------------------------------------------------------
    def visit_Program(self, node: Program):
        for stmt in node.stmts:
            stmt.accept(self)

    def visit_Block(self, node: Block):
        for stmt in node.stmts:
            stmt.accept(self)

    def visit_VarDecl(self, node: VarDecl):
        if node.init:
            src = node.init.accept(self)
            self._emit(TACInstr('copy', node.name, src))

    def visit_Assignment(self, node: Assignment):
        src = node.value.accept(self)
        self._emit(TACInstr('copy', node.name, src))

    def visit_IfStmt(self, node: IfStmt):
        """
        if (cond) T else E → padrão de salto condicional TAC:
          <cond>
          if_false cond goto L_else
          <then>
          goto L_end
        L_else:
          <else>
        L_end:
        """
        cond      = node.condition.accept(self)
        l_else    = self._new_label()
        l_end     = self._new_label()

        self._emit(TACInstr('if_false', arg1=cond, arg2=l_else))
        node.then_body.accept(self)
        self._emit(TACInstr('goto', arg1=l_end))
        self._emit(TACInstr('label', result=l_else))
        if node.else_body:
            node.else_body.accept(self)
        self._emit(TACInstr('label', result=l_end))

    def visit_WhileStmt(self, node: WhileStmt):
        """
        while (cond) body →
        L_start:
          <cond>
          if_false cond goto L_end
          <body>
          goto L_start
        L_end:
        """
        l_start = self._new_label()
        l_end   = self._new_label()

        self._emit(TACInstr('label', result=l_start))
        cond = node.condition.accept(self)
        self._emit(TACInstr('if_false', arg1=cond, arg2=l_end))
        node.body.accept(self)
        self._emit(TACInstr('goto', arg1=l_start))
        self._emit(TACInstr('label', result=l_end))

    def visit_PrintStmt(self, node: PrintStmt):
        val = node.value.accept(self)
        self._emit(TACInstr('print', arg1=val))

    def visit_ReadStmt(self, node: ReadStmt):
        self._emit(TACInstr('read', result=node.name))

    # -----------------------------------------------------------------------
    # Visitores de expressão — retornam o operando resultado
    # -----------------------------------------------------------------------
    def visit_IntLiteral(self, node: IntLiteral) -> Operand:
        return node.value   # constante inteira

    def visit_BoolLiteral(self, node: BoolLiteral) -> Operand:
        return node.value   # True / False

    def visit_StringLiteral(self, node: StringLiteral) -> Operand:
        return f'"{node.value}"'

    def visit_Identifier(self, node: Identifier) -> Operand:
        return node.name    # nome da variável

    def visit_UnaryOp(self, node: UnaryOp) -> Operand:
        operand = node.operand.accept(self)
        tmp     = self._new_temp()
        op_map  = {'!': 'unary_not', '-': 'unary_minus'}
        self._emit(TACInstr(op_map[node.op], result=tmp, arg1=operand))
        return tmp

    def visit_BinaryOp(self, node: BinaryOp) -> Operand:
        left  = node.left.accept(self)
        right = node.right.accept(self)
        tmp   = self._new_temp()
        self._emit(TACInstr(node.op, result=tmp, arg1=left, arg2=right))
        return tmp

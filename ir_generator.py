"""
=============================================================================
GERAÇÃO DE CÓDIGO INTERMEDIÁRIO — Compilador MiniLang
=============================================================================
Representa o código fonte em Código de Três Endereços (TAC).

IMPLEMENTAÇÃO MANUAL — sem dataclasses, sem typing, sem collections

Estrutura TACInstr implementada com __init__ explícito.
Gerador de temporários e rótulos implementado com contadores manuais.

Formato das instruções TAC:
  result = arg1 op arg2      (binária)
  result = op arg1           (unária)
  result = arg1              (cópia)
  label:                     (rótulo)
  goto label                 (salto incondicional)
  if_false cond goto label   (salto condicional)
  print arg1                 (saída)
  read result                (entrada)
=============================================================================
"""

from ast_nodes import (
    Program, Block, VarDecl, Assignment, IfStmt, WhileStmt,
    PrintStmt, ReadStmt, BinaryOp, UnaryOp,
    IntLiteral, BoolLiteral, StringLiteral, Identifier, Visitor
)


# ---------------------------------------------------------------------------
# Instrução TAC — classe com __init__ explícito (sem dataclass)
# ---------------------------------------------------------------------------
class TACInstr:
    """Uma instrução de Código de Três Endereços."""

    def __init__(self, op, result=None, arg1=None, arg2=None):
        self.op     = op       # string: operador ou tipo de instrução
        self.result = result   # string: nome do destino, ou None
        self.arg1   = arg1     # operando 1 (int, bool, string, ou None)
        self.arg2   = arg2     # operando 2 (idem)

    def __str__(self):
        """Formata a instrução de forma legível."""
        if self.op == 'label':
            return "%s:" % self.result

        if self.op == 'goto':
            return "  goto %s" % self.arg1

        if self.op == 'if_false':
            return "  if_false %s goto %s" % (self.arg1, self.arg2)

        if self.op == 'print':
            return "  print %s" % str(self.arg1)

        if self.op == 'read':
            return "  read %s" % self.result

        if self.op == 'copy':
            return "  %s = %s" % (self.result, str(self.arg1))

        if self.op == 'unary_minus':
            return "  %s = -%s" % (self.result, str(self.arg1))

        if self.op == 'unary_not':
            return "  %s = !%s" % (self.result, str(self.arg1))

        # Operação binária genérica
        return "  %s = %s %s %s" % (
            self.result, str(self.arg1), self.op, str(self.arg2)
        )


# ---------------------------------------------------------------------------
# Gerador de Código Intermediário — Visitor sobre a AST
# ---------------------------------------------------------------------------
class IRGenerator(Visitor):
    """
    Percorre a AST e emite instruções TAC.
    Temporários: t0, t1, t2, ...  (contador _temp_count)
    Rótulos:     L0, L1, L2, ...  (contador _label_count)
    """

    def __init__(self):
        self.instrucoes  = []   # lista de TACInstr
        self._temp_count  = 0
        self._label_count = 0

    # -----------------------------------------------------------------------
    # Geração de nomes únicos
    # -----------------------------------------------------------------------

    def _novo_temp(self):
        """Gera próximo temporário: t0, t1, t2, ..."""
        nome = "t%d" % self._temp_count
        self._temp_count += 1
        return nome

    def _novo_rotulo(self):
        """Gera próximo rótulo: L0, L1, L2, ..."""
        nome = "L%d" % self._label_count
        self._label_count += 1
        return nome

    def _emitir(self, instr):
        """Adiciona instrução à lista."""
        self.instrucoes.append(instr)

    def gerar(self, arvore):
        """Ponto de entrada: percorre a AST e retorna lista de TACInstr."""
        arvore.accept(self)
        return self.instrucoes

    def codigo_str(self):
        """Retorna o código TAC como string formatada."""
        resultado = ""
        for i in range(len(self.instrucoes)):
            if i == 0:
                resultado = str(self.instrucoes[0])
            else:
                resultado = resultado + "\n" + str(self.instrucoes[i])
        return resultado

    # -----------------------------------------------------------------------
    # Visitores de instrução
    # -----------------------------------------------------------------------

    def visit_Program(self, node):
        for stmt in node.stmts:
            stmt.accept(self)

    def visit_Block(self, node):
        for stmt in node.stmts:
            stmt.accept(self)

    def visit_VarDecl(self, node):
        if node.init is not None:
            src = node.init.accept(self)
            self._emitir(TACInstr('copy', node.name, src))

    def visit_Assignment(self, node):
        src = node.value.accept(self)
        self._emitir(TACInstr('copy', node.name, src))

    def visit_IfStmt(self, node):
        """
        Tradução do if-else para TAC com saltos:
          <avaliar condição>
          if_false cond goto L_else
          <then>
          goto L_fim
        L_else:
          <else>
        L_fim:
        """
        cond   = node.condition.accept(self)
        l_else = self._novo_rotulo()
        l_fim  = self._novo_rotulo()

        self._emitir(TACInstr('if_false', arg1=cond, arg2=l_else))
        node.then_body.accept(self)
        self._emitir(TACInstr('goto', arg1=l_fim))
        self._emitir(TACInstr('label', result=l_else))
        if node.else_body is not None:
            node.else_body.accept(self)
        self._emitir(TACInstr('label', result=l_fim))

    def visit_WhileStmt(self, node):
        """
        Tradução do while para TAC:
        L_inicio:
          <avaliar condição>
          if_false cond goto L_fim
          <corpo>
          goto L_inicio
        L_fim:
        """
        l_inicio = self._novo_rotulo()
        l_fim    = self._novo_rotulo()

        self._emitir(TACInstr('label', result=l_inicio))
        cond = node.condition.accept(self)
        self._emitir(TACInstr('if_false', arg1=cond, arg2=l_fim))
        node.body.accept(self)
        self._emitir(TACInstr('goto', arg1=l_inicio))
        self._emitir(TACInstr('label', result=l_fim))

    def visit_PrintStmt(self, node):
        val = node.value.accept(self)
        self._emitir(TACInstr('print', arg1=val))

    def visit_ReadStmt(self, node):
        self._emitir(TACInstr('read', result=node.name))

    # -----------------------------------------------------------------------
    # Visitores de expressão — retornam o operando resultado (nome ou literal)
    # -----------------------------------------------------------------------

    def visit_IntLiteral(self, node):
        return node.value        # inteiro diretamente (constante)

    def visit_BoolLiteral(self, node):
        return node.value        # True ou False

    def visit_StringLiteral(self, node):
        return '"' + node.value + '"'

    def visit_Identifier(self, node):
        return node.name         # nome da variável

    def visit_UnaryOp(self, node):
        operando = node.operand.accept(self)
        tmp = self._novo_temp()
        if node.op == '!':
            self._emitir(TACInstr('unary_not', result=tmp, arg1=operando))
        else:  # '-'
            self._emitir(TACInstr('unary_minus', result=tmp, arg1=operando))
        return tmp

    def visit_BinaryOp(self, node):
        esq = node.left.accept(self)
        dir = node.right.accept(self)
        tmp = self._novo_temp()
        self._emitir(TACInstr(node.op, result=tmp, arg1=esq, arg2=dir))
        return tmp

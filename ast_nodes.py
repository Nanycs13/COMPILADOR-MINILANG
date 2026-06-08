"""
=============================================================================
NÓS DA ÁRVORE DE SINTAXE ABSTRATA (AST) — MiniLang
=============================================================================
IMPLEMENTAÇÃO MANUAL — sem dataclasses, sem typing

Cada nó é uma classe Python com __init__ explícito.
O Visitor Pattern é implementado via método accept() em cada nó,
que chama o método visit_NomeDoNo(self) no objeto visitante.
=============================================================================
"""


# ---------------------------------------------------------------------------
# Classe base
# ---------------------------------------------------------------------------
class ASTNode:
    """Nó base da AST. Todos os nós herdam desta classe."""
    def accept(self, visitor):
        # Descobre o nome do método pelo tipo do nó
        nome_metodo = 'visit_' + self.__class__.__name__
        metodo = getattr(visitor, nome_metodo)
        return metodo(self)


# ---------------------------------------------------------------------------
# Nós de Expressão
# ---------------------------------------------------------------------------

class IntLiteral(ASTNode):
    """Literal inteiro: 42"""
    def __init__(self, value, line=0):
        self.value = value
        self.line  = line

class BoolLiteral(ASTNode):
    """Literal booleano: true / false"""
    def __init__(self, value, line=0):
        self.value = value
        self.line  = line

class StringLiteral(ASTNode):
    """Literal string: "hello" """
    def __init__(self, value, line=0):
        self.value = value
        self.line  = line

class Identifier(ASTNode):
    """Referência a variável: x"""
    def __init__(self, name, line=0):
        self.name = name
        self.line = line

class BinaryOp(ASTNode):
    """Operação binária: left op right  (ex: a + b, x == y)"""
    def __init__(self, op, left, right, line=0):
        self.op    = op
        self.left  = left
        self.right = right
        self.line  = line

class UnaryOp(ASTNode):
    """Operação unária: op operand  (ex: !x, -n)"""
    def __init__(self, op, operand, line=0):
        self.op      = op
        self.operand = operand
        self.line    = line


# ---------------------------------------------------------------------------
# Nós de Instrução
# ---------------------------------------------------------------------------

class VarDecl(ASTNode):
    """Declaração de variável: int x; ou int x = 5;"""
    def __init__(self, var_type, name, init, line=0):
        self.var_type = var_type   # "int" ou "bool"
        self.name     = name
        self.init     = init       # ASTNode ou None
        self.line     = line

class Assignment(ASTNode):
    """Atribuição: x = expr;"""
    def __init__(self, name, value, line=0):
        self.name  = name
        self.value = value
        self.line  = line

class IfStmt(ASTNode):
    """Condicional: if (cond) { ... } else { ... }"""
    def __init__(self, condition, then_body, else_body, line=0):
        self.condition = condition
        self.then_body = then_body
        self.else_body = else_body   # Block ou None
        self.line      = line

class WhileStmt(ASTNode):
    """Laço: while (cond) { ... }"""
    def __init__(self, condition, body, line=0):
        self.condition = condition
        self.body      = body
        self.line      = line

class PrintStmt(ASTNode):
    """Saída: print(expr);"""
    def __init__(self, value, line=0):
        self.value = value
        self.line  = line

class ReadStmt(ASTNode):
    """Entrada: read(var);"""
    def __init__(self, name, line=0):
        self.name = name
        self.line = line

class Block(ASTNode):
    """Bloco de instruções: { stmt* }"""
    def __init__(self, stmts, line=0):
        self.stmts = stmts   # lista de ASTNode
        self.line  = line

class Program(ASTNode):
    """Nó raiz: sequência de declarações e instruções."""
    def __init__(self, stmts):
        self.stmts = stmts   # lista de ASTNode


# ---------------------------------------------------------------------------
# Visitor base — subclasses sobrescrevem os métodos necessários
# ---------------------------------------------------------------------------
class Visitor:
    def visit_IntLiteral(self, node):    pass
    def visit_BoolLiteral(self, node):   pass
    def visit_StringLiteral(self, node): pass
    def visit_Identifier(self, node):    pass
    def visit_BinaryOp(self, node):      pass
    def visit_UnaryOp(self, node):       pass
    def visit_VarDecl(self, node):       pass
    def visit_Assignment(self, node):    pass
    def visit_IfStmt(self, node):        pass
    def visit_WhileStmt(self, node):     pass
    def visit_PrintStmt(self, node):     pass
    def visit_ReadStmt(self, node):      pass
    def visit_Block(self, node):         pass
    def visit_Program(self, node):       pass

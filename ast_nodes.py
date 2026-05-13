"""
=============================================================================
NÓS DA ÁRVORE DE SINTAXE ABSTRATA (AST) — MiniLang
=============================================================================
Cada classe representa um nó na AST. O Visitor Pattern permite que as
fases posteriores (semântica, geração de código) percorram a árvore sem
modificar os nós.
=============================================================================
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any


# ---------------------------------------------------------------------------
# Classe base de todos os nós
# ---------------------------------------------------------------------------
class ASTNode:
    """Nó base da AST. Todos os nós herdam desta classe."""
    def accept(self, visitor):
        method = 'visit_' + type(self).__name__
        return getattr(visitor, method)(self)


# ---------------------------------------------------------------------------
# Nós de Expressão
# ---------------------------------------------------------------------------
@dataclass
class IntLiteral(ASTNode):
    """Literal inteiro: 42"""
    value: int
    line: int = 0

@dataclass
class BoolLiteral(ASTNode):
    """Literal booleano: true / false"""
    value: bool
    line: int = 0

@dataclass
class StringLiteral(ASTNode):
    """Literal string: "hello" """
    value: str
    line: int = 0

@dataclass
class Identifier(ASTNode):
    """Referência a variável: x"""
    name: str
    line: int = 0

@dataclass
class BinaryOp(ASTNode):
    """Operação binária: left op right (ex: a + b, x == y)"""
    op:    str
    left:  ASTNode
    right: ASTNode
    line:  int = 0

@dataclass
class UnaryOp(ASTNode):
    """Operação unária: op operand (ex: !x, -n)"""
    op:      str
    operand: ASTNode
    line:    int = 0


# ---------------------------------------------------------------------------
# Nós de Declaração / Instrução
# ---------------------------------------------------------------------------
@dataclass
class VarDecl(ASTNode):
    """Declaração de variável: int x; ou int x = 5;"""
    var_type: str           # "int" ou "bool"
    name:     str
    init:     Optional[ASTNode]   # expressão inicial (pode ser None)
    line:     int = 0

@dataclass
class Assignment(ASTNode):
    """Atribuição: x = expr;"""
    name:  str
    value: ASTNode
    line:  int = 0

@dataclass
class IfStmt(ASTNode):
    """Condicional: if (cond) { ... } else { ... }"""
    condition:  ASTNode
    then_body:  'Block'
    else_body:  Optional['Block']
    line:       int = 0

@dataclass
class WhileStmt(ASTNode):
    """Laço: while (cond) { ... }"""
    condition: ASTNode
    body:      'Block'
    line:      int = 0

@dataclass
class PrintStmt(ASTNode):
    """Saída: print(expr);"""
    value: ASTNode
    line:  int = 0

@dataclass
class ReadStmt(ASTNode):
    """Entrada: read(var);"""
    name: str
    line: int = 0

@dataclass
class Block(ASTNode):
    """Bloco de instruções: { stmt* }"""
    stmts: List[ASTNode] = field(default_factory=list)
    line:  int = 0

@dataclass
class Program(ASTNode):
    """Nó raiz: sequência de declarações e instruções."""
    stmts: List[ASTNode] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Visitor base — implementar nas fases seguintes
# ---------------------------------------------------------------------------
class Visitor:
    """Implementação padrão do Visitor; subclasses sobrescrevem os métodos."""
    def visit_IntLiteral(self, node): pass
    def visit_BoolLiteral(self, node): pass
    def visit_StringLiteral(self, node): pass
    def visit_Identifier(self, node): pass
    def visit_BinaryOp(self, node): pass
    def visit_UnaryOp(self, node): pass
    def visit_VarDecl(self, node): pass
    def visit_Assignment(self, node): pass
    def visit_IfStmt(self, node): pass
    def visit_WhileStmt(self, node): pass
    def visit_PrintStmt(self, node): pass
    def visit_ReadStmt(self, node): pass
    def visit_Block(self, node): pass
    def visit_Program(self, node): pass

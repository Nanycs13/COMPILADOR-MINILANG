"""
=============================================================================
ANÁLISE SEMÂNTICA — Compilador MiniLang
=============================================================================
Responsabilidades:
  1. Tabela de Símbolos com suporte a escopo aninhado (pilha de escopos)
  2. Verificação de declaração prévia de variáveis
  3. Type Checking — compatibilidade de tipos em operações e atribuições
  4. Detecção de redeclaração no mesmo escopo
=============================================================================
"""

from typing import Optional, Dict, List
from ast_nodes import *


# ---------------------------------------------------------------------------
# Erros Semânticos
# ---------------------------------------------------------------------------
class SemanticError(Exception):
    def __init__(self, msg: str, line: int = 0):
        super().__init__(f"[Erro Semântico] L{line} — {msg}")
        self.line = line


# ---------------------------------------------------------------------------
# Tabela de Símbolos com escopos aninhados
# ---------------------------------------------------------------------------
class SymbolTable:
    """
    Implementa uma pilha de escopos (scope stack).
    Cada escopo é um dicionário {nome → tipo}.
    Ao entrar em um bloco, empilha; ao sair, desempilha.
    """

    def __init__(self):
        self._scopes: List[Dict[str, str]] = [{}]   # escopo global

    def enter_scope(self):
        """Abre um novo escopo (push)."""
        self._scopes.append({})

    def exit_scope(self):
        """Fecha o escopo atual (pop)."""
        if len(self._scopes) > 1:
            self._scopes.pop()

    def declare(self, name: str, var_type: str, line: int):
        """Declara variável no escopo atual. Erro se já declarada aqui."""
        current = self._scopes[-1]
        if name in current:
            raise SemanticError(
                f"Variável '{name}' já declarada neste escopo.", line
            )
        current[name] = var_type

    def lookup(self, name: str) -> Optional[str]:
        """Busca variável dos escopos mais internos para os mais externos."""
        for scope in reversed(self._scopes):
            if name in scope:
                return scope[name]
        return None

    def lookup_or_error(self, name: str, line: int) -> str:
        """Busca variável; lança SemanticError se não encontrada."""
        t = self.lookup(name)
        if t is None:
            raise SemanticError(f"Variável '{name}' não declarada.", line)
        return t

    def dump(self) -> str:
        """Representação textual da tabela para debug/relatório."""
        lines = []
        for i, scope in enumerate(self._scopes):
            label = "global" if i == 0 else f"escopo {i}"
            for name, typ in scope.items():
                lines.append(f"  [{label}] {name}: {typ}")
        return "\n".join(lines) if lines else "  (vazia)"


# ---------------------------------------------------------------------------
# Analisador Semântico — Visitor sobre a AST
# ---------------------------------------------------------------------------
class SemanticAnalyzer(Visitor):
    """
    Percorre a AST, gerencia a Tabela de Símbolos e verifica tipos.
    Retorna o tipo de cada expressão para uso no type checking.
    """

    # Tipos válidos na linguagem
    TYPES = {"int", "bool", "string"}

    # Operadores e os tipos que aceitam / o tipo que retornam
    ARITH_OPS   = {'+', '-', '*', '/'}
    RELAT_OPS   = {'<', '>', '<=', '>='}
    EQUAL_OPS   = {'==', '!='}
    LOGIC_OPS   = {'&&', '||'}

    def __init__(self):
        self.symbols = SymbolTable()
        self.errors: List[str] = []

    def analyze(self, tree: Program):
        """Ponto de entrada: visita o nó raiz."""
        tree.accept(self)
        if self.errors:
            raise SemanticError(
                "Erros semânticos encontrados:\n" +
                "\n".join(self.errors), 0
            )
        return self.symbols

    # -----------------------------------------------------------------------
    # Helpers de tipo
    # -----------------------------------------------------------------------
    def _expect_type(self, actual: str, expected: str, context: str, line: int):
        if actual != expected:
            self._err(f"{context}: esperado '{expected}', obtido '{actual}'.", line)

    def _err(self, msg: str, line: int = 0):
        self.errors.append(f"  L{line}: {msg}")

    # -----------------------------------------------------------------------
    # Visitores de instruções
    # -----------------------------------------------------------------------
    def visit_Program(self, node: Program):
        for stmt in node.stmts:
            stmt.accept(self)

    def visit_Block(self, node: Block):
        self.symbols.enter_scope()
        for stmt in node.stmts:
            stmt.accept(self)
        self.symbols.exit_scope()

    def visit_VarDecl(self, node: VarDecl):
        if node.var_type not in ("int", "bool"):
            self._err(f"Tipo desconhecido: '{node.var_type}'.", node.line)
            return

        if node.init:
            init_type = node.init.accept(self)
            if init_type and init_type != node.var_type:
                self._err(
                    f"Atribuição inválida: '{node.var_type} {node.name}' "
                    f"não pode receber valor do tipo '{init_type}'.",
                    node.line
                )
        try:
            self.symbols.declare(node.name, node.var_type, node.line)
        except SemanticError as e:
            self._err(str(e), node.line)

    def visit_Assignment(self, node: Assignment):
        try:
            var_type  = self.symbols.lookup_or_error(node.name, node.line)
            val_type  = node.value.accept(self)
            if val_type and val_type != var_type:
                self._err(
                    f"Atribuição de tipo incompatível: '{node.name}' é '{var_type}', "
                    f"mas o valor é '{val_type}'.",
                    node.line
                )
        except SemanticError as e:
            self._err(str(e), node.line)

    def visit_IfStmt(self, node: IfStmt):
        cond_type = node.condition.accept(self)
        if cond_type and cond_type != "bool":
            self._err(
                f"Condição do 'if' deve ser booleana, obtido '{cond_type}'.",
                node.line
            )
        node.then_body.accept(self)
        if node.else_body:
            node.else_body.accept(self)

    def visit_WhileStmt(self, node: WhileStmt):
        cond_type = node.condition.accept(self)
        if cond_type and cond_type != "bool":
            self._err(
                f"Condição do 'while' deve ser booleana, obtido '{cond_type}'.",
                node.line
            )
        node.body.accept(self)

    def visit_PrintStmt(self, node: PrintStmt):
        node.value.accept(self)   # aceita qualquer tipo

    def visit_ReadStmt(self, node: ReadStmt):
        try:
            var_type = self.symbols.lookup_or_error(node.name, node.line)
            if var_type not in ("int",):   # read suporta apenas int nesta versão
                self._err(
                    f"'read' suporta apenas variáveis do tipo 'int', "
                    f"mas '{node.name}' é '{var_type}'.",
                    node.line
                )
        except SemanticError as e:
            self._err(str(e), node.line)

    # -----------------------------------------------------------------------
    # Visitores de expressão — retornam o tipo da expressão
    # -----------------------------------------------------------------------
    def visit_IntLiteral(self, node: IntLiteral) -> str:
        return "int"

    def visit_BoolLiteral(self, node: BoolLiteral) -> str:
        return "bool"

    def visit_StringLiteral(self, node: StringLiteral) -> str:
        return "string"

    def visit_Identifier(self, node: Identifier) -> Optional[str]:
        try:
            return self.symbols.lookup_or_error(node.name, node.line)
        except SemanticError as e:
            self._err(str(e), node.line)
            return None

    def visit_UnaryOp(self, node: UnaryOp) -> Optional[str]:
        op_type = node.operand.accept(self)
        if node.op == '!':
            if op_type and op_type != "bool":
                self._err(f"'!' requer operando booleano, obtido '{op_type}'.", node.line)
            return "bool"
        if node.op == '-':
            if op_type and op_type != "int":
                self._err(f"Negação unária requer inteiro, obtido '{op_type}'.", node.line)
            return "int"
        return op_type

    def visit_BinaryOp(self, node: BinaryOp) -> Optional[str]:
        left_t  = node.left.accept(self)
        right_t = node.right.accept(self)
        op      = node.op

        if op in self.ARITH_OPS:
            # Ambos devem ser 'int', resultado é 'int'
            for t, side in [(left_t, "esquerda"), (right_t, "direita")]:
                if t and t != "int":
                    self._err(
                        f"Operador '{op}' requer inteiros; lado {side} é '{t}'.",
                        node.line
                    )
            return "int"

        if op in self.RELAT_OPS:
            # Ambos devem ser 'int', resultado é 'bool'
            for t, side in [(left_t, "esquerda"), (right_t, "direita")]:
                if t and t != "int":
                    self._err(
                        f"Operador '{op}' compara inteiros; lado {side} é '{t}'.",
                        node.line
                    )
            return "bool"

        if op in self.EQUAL_OPS:
            # Tipos devem ser iguais
            if left_t and right_t and left_t != right_t:
                self._err(
                    f"Comparação '{op}' entre tipos distintos: '{left_t}' e '{right_t}'.",
                    node.line
                )
            return "bool"

        if op in self.LOGIC_OPS:
            # Ambos devem ser 'bool'
            for t, side in [(left_t, "esquerda"), (right_t, "direita")]:
                if t and t != "bool":
                    self._err(
                        f"Operador '{op}' requer booleanos; lado {side} é '{t}'.",
                        node.line
                    )
            return "bool"

        self._err(f"Operador desconhecido: '{op}'.", node.line)
        return None

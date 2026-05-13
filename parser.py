"""
=============================================================================
ANÁLISE SINTÁTICA (Parser) — Compilador MiniLang
=============================================================================
Método: Parser Descendente Recursivo (Recursive Descent Parser)
Teoria aplicada: Gramáticas Livres de Contexto (GLC)

Gramática BNF da linguagem MiniLang:

  program     → stmt*
  stmt        → var_decl | assignment | if_stmt | while_stmt
              | print_stmt | read_stmt | block
  var_decl    → type IDENT ('=' expr)? ';'
  assignment  → IDENT '=' expr ';'
  if_stmt     → 'if' '(' expr ')' block ('else' block)?
  while_stmt  → 'while' '(' expr ')' block
  print_stmt  → 'print' '(' expr ')' ';'
  read_stmt   → 'read' '(' IDENT ')' ';'
  block       → '{' stmt* '}'
  type        → 'int' | 'bool'

  expr        → or_expr
  or_expr     → and_expr ('||' and_expr)*
  and_expr    → eq_expr ('&&' eq_expr)*
  eq_expr     → rel_expr (('==' | '!=') rel_expr)*
  rel_expr    → add_expr (('<' | '>' | '<=' | '>=') add_expr)*
  add_expr    → mul_expr (('+' | '-') mul_expr)*
  mul_expr    → unary (('*' | '/') unary)*
  unary       → ('!' | '-') unary | primary
  primary     → INTEGER | BOOLEAN | STRING | IDENT | '(' expr ')'
=============================================================================
"""

from typing import List, Optional
from lexer import TokenType, Token
from ast_nodes import *


class ParseError(Exception):
    def __init__(self, msg: str, token: Token):
        super().__init__(
            f"[Erro Sintático] L{token.line}:C{token.column} — {msg} "
            f"(encontrado: {token.type.name} '{token.value}')"
        )
        self.token = token


class Parser:
    """
    Parser Descendente Recursivo para MiniLang.
    Cada não-terminal da gramática tem um método correspondente.
    """

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos    = 0

    # -----------------------------------------------------------------------
    # Primitivas de navegação nos tokens
    # -----------------------------------------------------------------------
    def _current(self) -> Token:
        return self.tokens[self.pos]

    def _peek(self, offset: int = 1) -> Token:
        idx = self.pos + offset
        return self.tokens[idx] if idx < len(self.tokens) else self.tokens[-1]

    def _advance(self) -> Token:
        tok = self.tokens[self.pos]
        if tok.type != TokenType.EOF:
            self.pos += 1
        return tok

    def _check(self, *types: TokenType) -> bool:
        return self._current().type in types

    def _match(self, *types: TokenType) -> Optional[Token]:
        """Consome o token se for de um dos tipos esperados."""
        if self._check(*types):
            return self._advance()
        return None

    def _expect(self, ttype: TokenType, msg: str = "") -> Token:
        """Consome o token esperado ou lança ParseError."""
        if self._check(ttype):
            return self._advance()
        raise ParseError(
            msg or f"Esperado '{ttype.name}'",
            self._current()
        )

    # -----------------------------------------------------------------------
    # Ponto de entrada
    # -----------------------------------------------------------------------
    def parse(self) -> Program:
        stmts = []
        while not self._check(TokenType.EOF):
            stmts.append(self._parse_stmt())
        return Program(stmts)

    # -----------------------------------------------------------------------
    # Instruções
    # -----------------------------------------------------------------------
    def _parse_stmt(self) -> ASTNode:
        cur = self._current()

        if self._check(TokenType.INT, TokenType.BOOL):
            return self._parse_var_decl()

        if self._check(TokenType.IF):
            return self._parse_if()

        if self._check(TokenType.WHILE):
            return self._parse_while()

        if self._check(TokenType.PRINT):
            return self._parse_print()

        if self._check(TokenType.READ):
            return self._parse_read()

        if self._check(TokenType.LBRACE):
            return self._parse_block()

        # Atribuição: IDENT '=' expr ';'
        if self._check(TokenType.IDENTIFIER):
            return self._parse_assignment()

        raise ParseError("Instrução inválida", cur)

    def _parse_var_decl(self) -> VarDecl:
        """var_decl → type IDENT ('=' expr)? ';'"""
        type_tok = self._advance()          # 'int' ou 'bool'
        var_type = type_tok.value
        name_tok = self._expect(TokenType.IDENTIFIER, "Esperado nome de variável")
        name     = name_tok.value

        init = None
        if self._match(TokenType.ASSIGN):
            init = self._parse_expr()

        self._expect(TokenType.SEMICOLON, "Esperado ';' após declaração")
        return VarDecl(var_type, name, init, type_tok.line)

    def _parse_assignment(self) -> Assignment:
        """assignment → IDENT '=' expr ';'"""
        name_tok = self._advance()
        name     = name_tok.value
        self._expect(TokenType.ASSIGN, f"Esperado '=' após '{name}'")
        value = self._parse_expr()
        self._expect(TokenType.SEMICOLON, "Esperado ';' após atribuição")
        return Assignment(name, value, name_tok.line)

    def _parse_if(self) -> IfStmt:
        """if_stmt → 'if' '(' expr ')' block ('else' block)?"""
        tok = self._advance()   # 'if'
        self._expect(TokenType.LPAREN, "Esperado '(' após 'if'")
        cond = self._parse_expr()
        self._expect(TokenType.RPAREN, "Esperado ')' após condição")
        then_body = self._parse_block()
        else_body = None
        if self._match(TokenType.ELSE):
            else_body = self._parse_block()
        return IfStmt(cond, then_body, else_body, tok.line)

    def _parse_while(self) -> WhileStmt:
        """while_stmt → 'while' '(' expr ')' block"""
        tok = self._advance()   # 'while'
        self._expect(TokenType.LPAREN, "Esperado '(' após 'while'")
        cond = self._parse_expr()
        self._expect(TokenType.RPAREN, "Esperado ')' após condição")
        body = self._parse_block()
        return WhileStmt(cond, body, tok.line)

    def _parse_print(self) -> PrintStmt:
        """print_stmt → 'print' '(' expr ')' ';'"""
        tok = self._advance()   # 'print'
        self._expect(TokenType.LPAREN, "Esperado '(' após 'print'")
        val = self._parse_expr()
        self._expect(TokenType.RPAREN, "Esperado ')' após expressão")
        self._expect(TokenType.SEMICOLON, "Esperado ';'")
        return PrintStmt(val, tok.line)

    def _parse_read(self) -> ReadStmt:
        """read_stmt → 'read' '(' IDENT ')' ';'"""
        tok  = self._advance()   # 'read'
        self._expect(TokenType.LPAREN, "Esperado '(' após 'read'")
        name = self._expect(TokenType.IDENTIFIER, "Esperado nome de variável").value
        self._expect(TokenType.RPAREN, "Esperado ')' após variável")
        self._expect(TokenType.SEMICOLON, "Esperado ';'")
        return ReadStmt(name, tok.line)

    def _parse_block(self) -> Block:
        """block → '{' stmt* '}'"""
        tok = self._expect(TokenType.LBRACE, "Esperado '{'")
        stmts = []
        while not self._check(TokenType.RBRACE, TokenType.EOF):
            stmts.append(self._parse_stmt())
        self._expect(TokenType.RBRACE, "Esperado '}' para fechar bloco")
        return Block(stmts, tok.line)

    # -----------------------------------------------------------------------
    # Expressões — hierarquia de precedência (gramática LL)
    # -----------------------------------------------------------------------
    def _parse_expr(self) -> ASTNode:
        return self._parse_or()

    def _parse_or(self) -> ASTNode:
        """or_expr → and_expr ('||' and_expr)*"""
        left = self._parse_and()
        while tok := self._match(TokenType.OR):
            right = self._parse_and()
            left  = BinaryOp('||', left, right, tok.line)
        return left

    def _parse_and(self) -> ASTNode:
        """and_expr → eq_expr ('&&' eq_expr)*"""
        left = self._parse_equality()
        while tok := self._match(TokenType.AND):
            right = self._parse_equality()
            left  = BinaryOp('&&', left, right, tok.line)
        return left

    def _parse_equality(self) -> ASTNode:
        """eq_expr → rel_expr (('==' | '!=') rel_expr)*"""
        left = self._parse_relational()
        while tok := self._match(TokenType.EQUAL, TokenType.NOT_EQUAL):
            right = self._parse_relational()
            left  = BinaryOp(tok.value, left, right, tok.line)
        return left

    def _parse_relational(self) -> ASTNode:
        """rel_expr → add_expr (('<' | '>' | '<=' | '>=') add_expr)*"""
        left = self._parse_add()
        while tok := self._match(
                TokenType.LESS, TokenType.GREATER,
                TokenType.LESS_EQ, TokenType.GREATER_EQ):
            right = self._parse_add()
            left  = BinaryOp(tok.value, left, right, tok.line)
        return left

    def _parse_add(self) -> ASTNode:
        """add_expr → mul_expr (('+' | '-') mul_expr)*"""
        left = self._parse_mul()
        while tok := self._match(TokenType.PLUS, TokenType.MINUS):
            right = self._parse_mul()
            left  = BinaryOp(tok.value, left, right, tok.line)
        return left

    def _parse_mul(self) -> ASTNode:
        """mul_expr → unary (('*' | '/') unary)*"""
        left = self._parse_unary()
        while tok := self._match(TokenType.MULTIPLY, TokenType.DIVIDE):
            right = self._parse_unary()
            left  = BinaryOp(tok.value, left, right, tok.line)
        return left

    def _parse_unary(self) -> ASTNode:
        """unary → ('!' | '-') unary | primary"""
        if tok := self._match(TokenType.NOT):
            return UnaryOp('!', self._parse_unary(), tok.line)
        if tok := self._match(TokenType.MINUS):
            return UnaryOp('-', self._parse_unary(), tok.line)
        return self._parse_primary()

    def _parse_primary(self) -> ASTNode:
        """primary → INTEGER | BOOLEAN | STRING | IDENT | '(' expr ')'"""
        tok = self._current()

        if self._check(TokenType.INTEGER):
            self._advance()
            return IntLiteral(tok.value, tok.line)

        if self._check(TokenType.TRUE, TokenType.FALSE):
            self._advance()
            return BoolLiteral(tok.value, tok.line)

        if self._check(TokenType.STRING):
            self._advance()
            return StringLiteral(tok.value, tok.line)

        if self._check(TokenType.IDENTIFIER):
            self._advance()
            return Identifier(tok.value, tok.line)

        if self._match(TokenType.LPAREN):
            expr = self._parse_expr()
            self._expect(TokenType.RPAREN, "Esperado ')' após expressão")
            return expr

        raise ParseError("Expressão inválida", tok)

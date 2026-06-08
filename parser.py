"""
=============================================================================
ANÁLISE SINTÁTICA (Parser) — Compilador MiniLang
=============================================================================
Método: Parser Descendente Recursivo (Recursive Descent Parser)
Teoria: Gramáticas Livres de Contexto (GLC)

IMPLEMENTAÇÃO MANUAL — sem typing, sem bibliotecas de parsing

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
  rel_expr    → add_expr (('<'|'>'|'<='|'>=') add_expr)*
  add_expr    → mul_expr (('+' | '-') mul_expr)*
  mul_expr    → unary (('*' | '/') unary)*
  unary       → ('!' | '-') unary | primary
  primary     → INTEGER | BOOLEAN | STRING | IDENT | '(' expr ')'
=============================================================================
"""

from lexer     import TokenType, Token
from ast_nodes import (
    Program, Block, VarDecl, Assignment, IfStmt, WhileStmt,
    PrintStmt, ReadStmt, BinaryOp, UnaryOp,
    IntLiteral, BoolLiteral, StringLiteral, Identifier
)


# ---------------------------------------------------------------------------
# Erro Sintático
# ---------------------------------------------------------------------------
class ParseError(Exception):
    def __init__(self, msg, token):
        full = "[Erro Sintatico] L%d:C%d -- %s (encontrado: %s '%s')" % (
            token.line, token.column, msg,
            TokenType.name(token.type), token.value
        )
        Exception.__init__(self, full)
        self.token = token


# ---------------------------------------------------------------------------
# Parser Descendente Recursivo
# Cada não-terminal da gramática tem um método correspondente.
# ---------------------------------------------------------------------------
class Parser:

    def __init__(self, tokens):
        self.tokens = tokens   # lista de Token (inclui EOF)
        self.pos    = 0        # índice do token atual

    # -----------------------------------------------------------------------
    # Primitivas de navegação na lista de tokens
    # -----------------------------------------------------------------------

    def _current(self):
        """Retorna o token atual sem avançar."""
        return self.tokens[self.pos]

    def _advance(self):
        """Consome o token atual e retorna ele. Não avança além do EOF."""
        tok = self.tokens[self.pos]
        if tok.type != TokenType.EOF:
            self.pos += 1
        return tok

    def _check(self, *tipos):
        """Retorna True se o token atual é de algum dos tipos passados."""
        t = self._current().type
        for tipo in tipos:
            if t == tipo:
                return True
        return False

    def _match(self, *tipos):
        """Consome e retorna o token atual SE for de um dos tipos. Caso contrário None."""
        if self._check(*tipos):
            return self._advance()
        return None

    def _expect(self, tipo, msg=""):
        """Consome o token esperado ou lança ParseError."""
        if self._check(tipo):
            return self._advance()
        if not msg:
            msg = "Esperado '%s'" % TokenType.name(tipo)
        raise ParseError(msg, self._current())

    # -----------------------------------------------------------------------
    # Ponto de entrada: program → stmt*
    # -----------------------------------------------------------------------
    def parse(self):
        stmts = []
        while not self._check(TokenType.EOF):
            stmts.append(self._parse_stmt())
        return Program(stmts)

    # -----------------------------------------------------------------------
    # Instruções
    # -----------------------------------------------------------------------

    def _parse_stmt(self):
        # var_decl: começa com tipo (int | bool)
        if self._check(TokenType.INT, TokenType.BOOL):
            return self._parse_var_decl()

        # if_stmt
        if self._check(TokenType.IF):
            return self._parse_if()

        # while_stmt
        if self._check(TokenType.WHILE):
            return self._parse_while()

        # print_stmt
        if self._check(TokenType.PRINT):
            return self._parse_print()

        # read_stmt
        if self._check(TokenType.READ):
            return self._parse_read()

        # block
        if self._check(TokenType.LBRACE):
            return self._parse_block()

        # assignment: IDENT '=' expr ';'
        if self._check(TokenType.IDENTIFIER):
            return self._parse_assignment()

        raise ParseError("Instrucao invalida", self._current())

    def _parse_var_decl(self):
        """var_decl → type IDENT ('=' expr)? ';'"""
        type_tok = self._advance()                        # 'int' ou 'bool'
        var_type = type_tok.value                         # "int" ou "bool"
        name_tok = self._expect(TokenType.IDENTIFIER, "Esperado nome de variavel")
        name     = name_tok.value

        init = None
        if self._match(TokenType.ASSIGN):
            init = self._parse_expr()

        self._expect(TokenType.SEMICOLON, "Esperado ';' apos declaracao")
        return VarDecl(var_type, name, init, type_tok.line)

    def _parse_assignment(self):
        """assignment → IDENT '=' expr ';'"""
        name_tok = self._advance()
        name     = name_tok.value
        self._expect(TokenType.ASSIGN, "Esperado '=' apos '%s'" % name)
        value = self._parse_expr()
        self._expect(TokenType.SEMICOLON, "Esperado ';' apos atribuicao")
        return Assignment(name, value, name_tok.line)

    def _parse_if(self):
        """if_stmt → 'if' '(' expr ')' block ('else' block)?"""
        tok = self._advance()   # consome 'if'
        self._expect(TokenType.LPAREN, "Esperado '(' apos 'if'")
        cond = self._parse_expr()
        self._expect(TokenType.RPAREN, "Esperado ')' apos condicao")
        then_body = self._parse_block()
        else_body = None
        if self._match(TokenType.ELSE):
            else_body = self._parse_block()
        return IfStmt(cond, then_body, else_body, tok.line)

    def _parse_while(self):
        """while_stmt → 'while' '(' expr ')' block"""
        tok = self._advance()   # consome 'while'
        self._expect(TokenType.LPAREN, "Esperado '(' apos 'while'")
        cond = self._parse_expr()
        self._expect(TokenType.RPAREN, "Esperado ')' apos condicao")
        body = self._parse_block()
        return WhileStmt(cond, body, tok.line)

    def _parse_print(self):
        """print_stmt → 'print' '(' expr ')' ';'"""
        tok = self._advance()   # consome 'print'
        self._expect(TokenType.LPAREN, "Esperado '(' apos 'print'")
        val = self._parse_expr()
        self._expect(TokenType.RPAREN, "Esperado ')' apos expressao")
        self._expect(TokenType.SEMICOLON, "Esperado ';'")
        return PrintStmt(val, tok.line)

    def _parse_read(self):
        """read_stmt → 'read' '(' IDENT ')' ';'"""
        tok  = self._advance()   # consome 'read'
        self._expect(TokenType.LPAREN, "Esperado '(' apos 'read'")
        name = self._expect(TokenType.IDENTIFIER, "Esperado nome de variavel").value
        self._expect(TokenType.RPAREN, "Esperado ')' apos variavel")
        self._expect(TokenType.SEMICOLON, "Esperado ';'")
        return ReadStmt(name, tok.line)

    def _parse_block(self):
        """block → '{' stmt* '}'"""
        tok = self._expect(TokenType.LBRACE, "Esperado '{'")
        stmts = []
        while not self._check(TokenType.RBRACE, TokenType.EOF):
            stmts.append(self._parse_stmt())
        self._expect(TokenType.RBRACE, "Esperado '}' para fechar bloco")
        return Block(stmts, tok.line)

    # -----------------------------------------------------------------------
    # Expressões — hierarquia de precedência codificada na gramática
    # Cada nível chama o próximo (de menor para maior precedência)
    # -----------------------------------------------------------------------

    def _parse_expr(self):
        return self._parse_or()

    def _parse_or(self):
        """or_expr → and_expr ('||' and_expr)*"""
        left = self._parse_and()
        tok  = self._match(TokenType.OR)
        while tok is not None:
            right = self._parse_and()
            left  = BinaryOp('||', left, right, tok.line)
            tok   = self._match(TokenType.OR)
        return left

    def _parse_and(self):
        """and_expr → eq_expr ('&&' eq_expr)*"""
        left = self._parse_equality()
        tok  = self._match(TokenType.AND)
        while tok is not None:
            right = self._parse_equality()
            left  = BinaryOp('&&', left, right, tok.line)
            tok   = self._match(TokenType.AND)
        return left

    def _parse_equality(self):
        """eq_expr → rel_expr (('==' | '!=') rel_expr)*"""
        left = self._parse_relational()
        tok  = self._match(TokenType.EQUAL, TokenType.NOT_EQUAL)
        while tok is not None:
            right = self._parse_relational()
            left  = BinaryOp(tok.value, left, right, tok.line)
            tok   = self._match(TokenType.EQUAL, TokenType.NOT_EQUAL)
        return left

    def _parse_relational(self):
        """rel_expr → add_expr (('<'|'>'|'<='|'>=') add_expr)*"""
        left = self._parse_add()
        tok  = self._match(TokenType.LESS, TokenType.GREATER,
                           TokenType.LESS_EQ, TokenType.GREATER_EQ)
        while tok is not None:
            right = self._parse_add()
            left  = BinaryOp(tok.value, left, right, tok.line)
            tok   = self._match(TokenType.LESS, TokenType.GREATER,
                                TokenType.LESS_EQ, TokenType.GREATER_EQ)
        return left

    def _parse_add(self):
        """add_expr → mul_expr (('+' | '-') mul_expr)*"""
        left = self._parse_mul()
        tok  = self._match(TokenType.PLUS, TokenType.MINUS)
        while tok is not None:
            right = self._parse_mul()
            left  = BinaryOp(tok.value, left, right, tok.line)
            tok   = self._match(TokenType.PLUS, TokenType.MINUS)
        return left

    def _parse_mul(self):
        """mul_expr → unary (('*' | '/') unary)*"""
        left = self._parse_unary()
        tok  = self._match(TokenType.MULTIPLY, TokenType.DIVIDE)
        while tok is not None:
            right = self._parse_unary()
            left  = BinaryOp(tok.value, left, right, tok.line)
            tok   = self._match(TokenType.MULTIPLY, TokenType.DIVIDE)
        return left

    def _parse_unary(self):
        """unary → ('!' | '-') unary | primary"""
        tok = self._match(TokenType.NOT)
        if tok is not None:
            return UnaryOp('!', self._parse_unary(), tok.line)
        tok = self._match(TokenType.MINUS)
        if tok is not None:
            return UnaryOp('-', self._parse_unary(), tok.line)
        return self._parse_primary()

    def _parse_primary(self):
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
            self._expect(TokenType.RPAREN, "Esperado ')' apos expressao")
            return expr

        raise ParseError("Expressao invalida", tok)



from lexer     import TokenType, Token
from ast_nodes import (
    Program, Block, VarDecl, Assignment, IfStmt, WhileStmt,
    PrintStmt, ReadStmt, BinaryOp, UnaryOp,
    IntLiteral, BoolLiteral, StringLiteral, Identifier
)


class ParseError(Exception):
    def __init__(self, msg, token):
        full = "[Erro Sintatico] L%d:C%d -- %s (encontrado: %s '%s')" % (
            token.line, token.column, msg,
            TokenType.name(token.type), token.value
        )
        Exception.__init__(self, full)
        self.token = token


class Parser:

    def __init__(self, tokens):
        self.tokens = tokens   
        self.pos    = 0        


    def _current(self):
        return self.tokens[self.pos]

    def _advance(self):
        tok = self.tokens[self.pos]
        if tok.type != TokenType.EOF:
            self.pos += 1
        return tok

    def _check(self, *tipos):
        t = self._current().type
        for tipo in tipos:
            if t == tipo:
                return True
        return False

    def _match(self, *tipos):
        if self._check(*tipos):
            return self._advance()
        return None

    def _expect(self, tipo, msg=""):
        if self._check(tipo):
            return self._advance()
        if not msg:
            msg = "Esperado '%s'" % TokenType.name(tipo)
        raise ParseError(msg, self._current())

    def parse(self):
        stmts = []
        while not self._check(TokenType.EOF):
            stmts.append(self._parse_stmt())
        return Program(stmts)


    def _parse_stmt(self):
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

        if self._check(TokenType.IDENTIFIER):
            return self._parse_assignment()

        raise ParseError("Instrucao invalida", self._current())

    def _parse_var_decl(self):
        type_tok = self._advance()                       
        var_type = type_tok.value                         
        name_tok = self._expect(TokenType.IDENTIFIER, "Esperado nome de variavel")
        name     = name_tok.value

        init = None
        if self._match(TokenType.ASSIGN):
            init = self._parse_expr()

        self._expect(TokenType.SEMICOLON, "Esperado ';' apos declaracao")
        return VarDecl(var_type, name, init, type_tok.line)

    def _parse_assignment(self):
        name_tok = self._advance()
        name     = name_tok.value
        self._expect(TokenType.ASSIGN, "Esperado '=' apos '%s'" % name)
        value = self._parse_expr()
        self._expect(TokenType.SEMICOLON, "Esperado ';' apos atribuicao")
        return Assignment(name, value, name_tok.line)

    def _parse_if(self):
        tok = self._advance()   
        self._expect(TokenType.LPAREN, "Esperado '(' apos 'if'")
        cond = self._parse_expr()
        self._expect(TokenType.RPAREN, "Esperado ')' apos condicao")
        then_body = self._parse_block()
        else_body = None
        if self._match(TokenType.ELSE):
            else_body = self._parse_block()
        return IfStmt(cond, then_body, else_body, tok.line)

    def _parse_while(self):
        tok = self._advance()   
        self._expect(TokenType.LPAREN, "Esperado '(' apos 'while'")
        cond = self._parse_expr()
        self._expect(TokenType.RPAREN, "Esperado ')' apos condicao")
        body = self._parse_block()
        return WhileStmt(cond, body, tok.line)

    def _parse_print(self):
        tok = self._advance()   
        self._expect(TokenType.LPAREN, "Esperado '(' apos 'print'")
        val = self._parse_expr()
        self._expect(TokenType.RPAREN, "Esperado ')' apos expressao")
        self._expect(TokenType.SEMICOLON, "Esperado ';'")
        return PrintStmt(val, tok.line)

    def _parse_read(self):
        tok  = self._advance()   
        self._expect(TokenType.LPAREN, "Esperado '(' apos 'read'")
        name = self._expect(TokenType.IDENTIFIER, "Esperado nome de variavel").value
        self._expect(TokenType.RPAREN, "Esperado ')' apos variavel")
        self._expect(TokenType.SEMICOLON, "Esperado ';'")
        return ReadStmt(name, tok.line)

    def _parse_block(self):
        tok = self._expect(TokenType.LBRACE, "Esperado '{'")
        stmts = []
        while not self._check(TokenType.RBRACE, TokenType.EOF):
            stmts.append(self._parse_stmt())
        self._expect(TokenType.RBRACE, "Esperado '}' para fechar bloco")
        return Block(stmts, tok.line)


    def _parse_expr(self):
        return self._parse_or()

    def _parse_or(self):
        left = self._parse_and()
        tok  = self._match(TokenType.OR)
        while tok is not None:
            right = self._parse_and()
            left  = BinaryOp('||', left, right, tok.line)
            tok   = self._match(TokenType.OR)
        return left

    def _parse_and(self):
        left = self._parse_equality()
        tok  = self._match(TokenType.AND)
        while tok is not None:
            right = self._parse_equality()
            left  = BinaryOp('&&', left, right, tok.line)
            tok   = self._match(TokenType.AND)
        return left

    def _parse_equality(self):
        left = self._parse_relational()
        tok  = self._match(TokenType.EQUAL, TokenType.NOT_EQUAL)
        while tok is not None:
            right = self._parse_relational()
            left  = BinaryOp(tok.value, left, right, tok.line)
            tok   = self._match(TokenType.EQUAL, TokenType.NOT_EQUAL)
        return left

    def _parse_relational(self):
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
        left = self._parse_mul()
        tok  = self._match(TokenType.PLUS, TokenType.MINUS)
        while tok is not None:
            right = self._parse_mul()
            left  = BinaryOp(tok.value, left, right, tok.line)
            tok   = self._match(TokenType.PLUS, TokenType.MINUS)
        return left

    def _parse_mul(self):
        left = self._parse_unary()
        tok  = self._match(TokenType.MULTIPLY, TokenType.DIVIDE)
        while tok is not None:
            right = self._parse_unary()
            left  = BinaryOp(tok.value, left, right, tok.line)
            tok   = self._match(TokenType.MULTIPLY, TokenType.DIVIDE)
        return left

    def _parse_unary(self):
        tok = self._match(TokenType.NOT)
        if tok is not None:
            return UnaryOp('!', self._parse_unary(), tok.line)
        tok = self._match(TokenType.MINUS)
        if tok is not None:
            return UnaryOp('-', self._parse_unary(), tok.line)
        return self._parse_primary()

    def _parse_primary(self):
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

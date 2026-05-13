"""
=============================================================================
ANÁLISE LÉXICA (Scanner) — Compilador MiniLang
=============================================================================
Teoria aplicada: Expressões Regulares e Autômatos Finitos Determinísticos (AFD)

O scanner transforma o fluxo de caracteres de entrada em uma sequência de
tokens, implementando um AFD para reconhecer os lexemas da linguagem.
=============================================================================
"""

import re
from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional


# ---------------------------------------------------------------------------
# Tipos de Tokens (terminais da gramática)
# ---------------------------------------------------------------------------
class TokenType(Enum):
    # Literais
    INTEGER     = auto()   # ex: 42, 0, -1
    BOOLEAN     = auto()   # true, false
    STRING      = auto()   # "hello"

    # Identificadores e palavras reservadas
    IDENTIFIER  = auto()   # ex: x, counter, myVar

    # Palavras reservadas
    INT         = auto()   # int
    BOOL        = auto()   # bool
    IF          = auto()   # if
    ELSE        = auto()   # else
    WHILE       = auto()   # while
    PRINT       = auto()   # print
    READ        = auto()   # read
    TRUE        = auto()   # true
    FALSE       = auto()   # false

    # Operadores aritméticos
    PLUS        = auto()   # +
    MINUS       = auto()   # -
    MULTIPLY    = auto()   # *
    DIVIDE      = auto()   # /

    # Operadores relacionais / lógicos
    EQUAL       = auto()   # ==
    NOT_EQUAL   = auto()   # !=
    LESS        = auto()   # <
    GREATER     = auto()   # >
    LESS_EQ     = auto()   # <=
    GREATER_EQ  = auto()   # >=
    AND         = auto()   # &&
    OR          = auto()   # ||
    NOT         = auto()   # !

    # Atribuição
    ASSIGN      = auto()   # =

    # Delimitadores
    LPAREN      = auto()   # (
    RPAREN      = auto()   # )
    LBRACE      = auto()   # {
    RBRACE      = auto()   # }
    SEMICOLON   = auto()   # ;
    COMMA       = auto()   # ,

    # Fim de arquivo
    EOF         = auto()


# Mapeamento de palavras reservadas → TokenType
KEYWORDS = {
    "int":   TokenType.INT,
    "bool":  TokenType.BOOL,
    "if":    TokenType.IF,
    "else":  TokenType.ELSE,
    "while": TokenType.WHILE,
    "print": TokenType.PRINT,
    "read":  TokenType.READ,
    "true":  TokenType.TRUE,
    "false": TokenType.FALSE,
}


# ---------------------------------------------------------------------------
# Estrutura de um Token
# ---------------------------------------------------------------------------
@dataclass
class Token:
    type:    TokenType
    value:   object        # valor léxico (int, str, bool, None)
    line:    int           # linha no código-fonte
    column:  int           # coluna no código-fonte

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, L{self.line}:C{self.column})"


# ---------------------------------------------------------------------------
# Erro Léxico
# ---------------------------------------------------------------------------
class LexerError(Exception):
    def __init__(self, msg: str, line: int, column: int):
        super().__init__(f"[Erro Léxico] L{line}:C{column} — {msg}")
        self.line   = line
        self.column = column


# ---------------------------------------------------------------------------
# Lexer — Autômato Finito Determinístico Manual
# ---------------------------------------------------------------------------
class Lexer:
    """
    Implementa um AFD manual para tokenização da linguagem MiniLang.

    Estados internos (implícitos nos métodos):
      START  → estado inicial
      NUM    → lendo dígitos
      IDENT  → lendo identificador/palavra-reservada
      STR    → lendo string literal
      OP     → avaliando operadores de 1 ou 2 caracteres
      COMM   → consumindo comentário de linha (//)
    """

    def __init__(self, source: str):
        self.source  = source       # código-fonte completo
        self.pos     = 0            # posição atual no source
        self.line    = 1            # linha atual
        self.column  = 1            # coluna atual
        self.tokens: List[Token] = []

    # -----------------------------------------------------------------------
    # Métodos auxiliares de navegação
    # -----------------------------------------------------------------------
    def _current(self) -> Optional[str]:
        """Retorna o caractere atual sem avançar (peek)."""
        return self.source[self.pos] if self.pos < len(self.source) else None

    def _peek(self, offset: int = 1) -> Optional[str]:
        """Lookahead de N caracteres."""
        idx = self.pos + offset
        return self.source[idx] if idx < len(self.source) else None

    def _advance(self) -> str:
        """Consome o caractere atual e atualiza linha/coluna."""
        ch = self.source[self.pos]
        self.pos    += 1
        self.column += 1
        if ch == '\n':
            self.line  += 1
            self.column = 1
        return ch

    def _make_token(self, ttype: TokenType, value=None,
                    line=None, col=None) -> Token:
        return Token(ttype, value,
                     line or self.line,
                     col  or self.column)

    # -----------------------------------------------------------------------
    # Tokenização principal
    # -----------------------------------------------------------------------
    def tokenize(self) -> List[Token]:
        """
        Ponto de entrada: percorre o source e retorna lista de Tokens.
        Estado START do AFD — decide a transição pelo primeiro caractere.
        """
        while (ch := self._current()) is not None:
            tok_line = self.line
            tok_col  = self.column

            # ── espaços em branco → ignorar
            if ch.isspace():
                self._advance()

            # ── comentário de linha: // até \n
            elif ch == '/' and self._peek() == '/':
                self._skip_line_comment()

            # ── comentário de bloco: /* ... */
            elif ch == '/' and self._peek() == '*':
                self._skip_block_comment()

            # ── inteiro
            elif ch.isdigit():
                self.tokens.append(self._read_integer(tok_line, tok_col))

            # ── string literal "..."
            elif ch == '"':
                self.tokens.append(self._read_string(tok_line, tok_col))

            # ── identificador ou palavra reservada
            elif ch.isalpha() or ch == '_':
                self.tokens.append(self._read_identifier(tok_line, tok_col))

            # ── operadores e delimitadores
            else:
                tok = self._read_operator(tok_line, tok_col)
                if tok:
                    self.tokens.append(tok)

        self.tokens.append(self._make_token(TokenType.EOF, None))
        return self.tokens

    # -----------------------------------------------------------------------
    # Estados do AFD para cada categoria de lexema
    # -----------------------------------------------------------------------

    def _skip_line_comment(self):
        """Consome '//' até o fim da linha."""
        while self._current() and self._current() != '\n':
            self._advance()

    def _skip_block_comment(self):
        """Consome '/* ... */' inclusive multilinhas."""
        self._advance()   # /
        self._advance()   # *
        while self._current():
            if self._current() == '*' and self._peek() == '/':
                self._advance()  # *
                self._advance()  # /
                return
            self._advance()
        raise LexerError("Comentário de bloco não fechado", self.line, self.column)

    def _read_integer(self, line: int, col: int) -> Token:
        """
        Estado NUM: consome [0-9]+
        Autômato: q0 -[0-9]-> q1 (loop) -[^0-9]-> aceito
        """
        buf = []
        while self._current() and self._current().isdigit():
            buf.append(self._advance())
        return Token(TokenType.INTEGER, int("".join(buf)), line, col)

    def _read_string(self, line: int, col: int) -> Token:
        """
        Estado STR: consome '"' [^"]* '"'
        Suporta sequências de escape \\, \\n, \\t, \\"
        """
        self._advance()   # abre "
        buf = []
        while True:
            ch = self._current()
            if ch is None:
                raise LexerError("String literal não fechada", line, col)
            if ch == '"':
                self._advance()   # fecha "
                break
            if ch == '\\':
                self._advance()
                esc = self._advance()
                escapes = {'n': '\n', 't': '\t', '\\': '\\', '"': '"'}
                buf.append(escapes.get(esc, esc))
            else:
                buf.append(self._advance())
        return Token(TokenType.STRING, "".join(buf), line, col)

    def _read_identifier(self, line: int, col: int) -> Token:
        """
        Estado IDENT: consome [a-zA-Z_][a-zA-Z0-9_]*
        Verifica na tabela de palavras reservadas após consumir.
        """
        buf = []
        while self._current() and (self._current().isalnum() or self._current() == '_'):
            buf.append(self._advance())
        lexeme = "".join(buf)
        ttype  = KEYWORDS.get(lexeme, TokenType.IDENTIFIER)

        # Ajusta o valor semântico para booleanos
        value  = lexeme
        if ttype == TokenType.TRUE:
            value = True
        elif ttype == TokenType.FALSE:
            value = False

        return Token(ttype, value, line, col)

    def _read_operator(self, line: int, col: int) -> Optional[Token]:
        """
        Estado OP: operadores de 1 ou 2 caracteres.
        Usa lookahead de 1 para decidir entre == e =, != e !, etc.
        """
        ch   = self._advance()
        next = self._current()

        # Dois caracteres
        if ch == '=' and next == '=':  self._advance(); return Token(TokenType.EQUAL,      '==', line, col)
        if ch == '!' and next == '=':  self._advance(); return Token(TokenType.NOT_EQUAL,  '!=', line, col)
        if ch == '<' and next == '=':  self._advance(); return Token(TokenType.LESS_EQ,    '<=', line, col)
        if ch == '>' and next == '=':  self._advance(); return Token(TokenType.GREATER_EQ, '>=', line, col)
        if ch == '&' and next == '&':  self._advance(); return Token(TokenType.AND,        '&&', line, col)
        if ch == '|' and next == '|':  self._advance(); return Token(TokenType.OR,         '||', line, col)

        # Um caractere
        single = {
            '+': TokenType.PLUS, '-': TokenType.MINUS,
            '*': TokenType.MULTIPLY, '/': TokenType.DIVIDE,
            '<': TokenType.LESS,    '>': TokenType.GREATER,
            '=': TokenType.ASSIGN,  '!': TokenType.NOT,
            '(': TokenType.LPAREN,  ')': TokenType.RPAREN,
            '{': TokenType.LBRACE,  '}': TokenType.RBRACE,
            ';': TokenType.SEMICOLON, ',': TokenType.COMMA,
        }
        if ch in single:
            return Token(single[ch], ch, line, col)

        raise LexerError(f"Caractere desconhecido: {ch!r}", line, col)

"""
=============================================================================
ANÁLISE LÉXICA (Scanner) — Compilador MiniLang
=============================================================================
Teoria aplicada: Expressões Regulares e Autômatos Finitos Determinísticos (AFD)

IMPLEMENTAÇÃO MANUAL — sem uso de: enum, dataclasses, re, typing
  - TokenType: classe com constantes inteiras (simula enum manualmente)
  - Token: classe comum com __init__ explícito
  - Lexer: AFD implementado caractere a caractere, sem regex
=============================================================================
"""


# ---------------------------------------------------------------------------
# TokenType — constantes inteiras que identificam cada tipo de token
# (implementação manual de enum usando atributos de classe)
# ---------------------------------------------------------------------------
class TokenType:
    # Literais
    INTEGER      = 1
    BOOLEAN      = 2
    STRING       = 3

    # Identificador
    IDENTIFIER   = 4

    # Palavras reservadas
    INT          = 10
    BOOL         = 11
    IF           = 12
    ELSE         = 13
    WHILE        = 14
    PRINT        = 15
    READ         = 16
    TRUE         = 17
    FALSE        = 18

    # Operadores aritméticos
    PLUS         = 20
    MINUS        = 21
    MULTIPLY     = 22
    DIVIDE       = 23

    # Operadores relacionais
    EQUAL        = 30   # ==
    NOT_EQUAL    = 31   # !=
    LESS         = 32   # <
    GREATER      = 33   # >
    LESS_EQ      = 34   # <=
    GREATER_EQ   = 35   # >=

    # Operadores lógicos
    AND          = 36   # &&
    OR           = 37   # ||
    NOT          = 38   # !

    # Atribuição
    ASSIGN       = 40   # =

    # Delimitadores
    LPAREN       = 50   # (
    RPAREN       = 51   # )
    LBRACE       = 52   # {
    RBRACE       = 53   # }
    SEMICOLON    = 54   # ;
    COMMA        = 55   # ,

    # Fim de arquivo
    EOF          = 99

    # Mapa reverso: código → nome legível (para mensagens de erro)
    _names = {
        1:"INTEGER", 2:"BOOLEAN", 3:"STRING", 4:"IDENTIFIER",
        10:"INT", 11:"BOOL", 12:"IF", 13:"ELSE", 14:"WHILE",
        15:"PRINT", 16:"READ", 17:"TRUE", 18:"FALSE",
        20:"PLUS", 21:"MINUS", 22:"MULTIPLY", 23:"DIVIDE",
        30:"EQUAL", 31:"NOT_EQUAL", 32:"LESS", 33:"GREATER",
        34:"LESS_EQ", 35:"GREATER_EQ", 36:"AND", 37:"OR", 38:"NOT",
        40:"ASSIGN", 50:"LPAREN", 51:"RPAREN", 52:"LBRACE",
        53:"RBRACE", 54:"SEMICOLON", 55:"COMMA", 99:"EOF",
    }

    @staticmethod
    def name(code):
        return TokenType._names.get(code, "UNKNOWN")


# Mapeamento de palavras reservadas → código de token
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
# Token — estrutura de dados simples com __init__ explícito
# ---------------------------------------------------------------------------
class Token:
    def __init__(self, ttype, value, line, column):
        self.type   = ttype    # int (código TokenType)
        self.value  = value    # valor semântico (int, bool, str, None)
        self.line   = line
        self.column = column

    def __repr__(self):
        return "Token(%s, %r, L%d:C%d)" % (
            TokenType.name(self.type), self.value, self.line, self.column
        )


# ---------------------------------------------------------------------------
# Erro Léxico
# ---------------------------------------------------------------------------
class LexerError(Exception):
    def __init__(self, msg, line, column):
        full = "[Erro Lexico] L%d:C%d -- %s" % (line, column, msg)
        Exception.__init__(self, full)
        self.line   = line
        self.column = column


# ---------------------------------------------------------------------------
# Funções auxiliares — escritas manualmente (sem re, sem str.isdigit etc.)
# Implementam os predicados do AFD para cada classe de caractere
# ---------------------------------------------------------------------------

def _eh_digito(ch):
    """Verifica se ch é dígito decimal [0-9]."""
    return ch is not None and '0' <= ch <= '9'

def _eh_letra(ch):
    """Verifica se ch é letra [a-zA-Z]."""
    if ch is None:
        return False
    return ('a' <= ch <= 'z') or ('A' <= ch <= 'Z')

def _eh_alfanum(ch):
    """Verifica se ch é letra, dígito ou underscore."""
    return _eh_letra(ch) or _eh_digito(ch) or ch == '_'

def _eh_espaco(ch):
    """Verifica se ch é espaço em branco."""
    return ch in (' ', '\t', '\n', '\r', '\f', '\v')


# ---------------------------------------------------------------------------
# Lexer — Autômato Finito Determinístico implementado manualmente
# ---------------------------------------------------------------------------
class Lexer:
    """
    AFD manual para tokenização da linguagem MiniLang.

    O método tokenize() é o estado START do AFD.
    Cada método _read_* implementa um estado específico do autômato:

      START     → decide transição pelo primeiro caractere
      NUM       → _read_integer  : consome [0-9]+
      IDENT     → _read_identifier: consome [a-zA-Z_][a-zA-Z0-9_]*
      STR       → _read_string  : consome '"' ... '"'
      OP        → _read_operator: avalia operadores de 1 ou 2 chars
      COMM_LINE → _skip_line_comment : consome até '\n'
      COMM_BLOC → _skip_block_comment: consome /* ... */
    """

    def __init__(self, source):
        self.source  = source       # string com o código-fonte completo
        self.pos     = 0            # posição atual (índice em source)
        self.line    = 1            # linha atual (começa em 1)
        self.column  = 1            # coluna atual (começa em 1)
        self.tokens  = []           # lista de tokens gerados

    # -----------------------------------------------------------------------
    # Operações primitivas de navegação no source (usadas pelo AFD)
    # -----------------------------------------------------------------------

    def _current(self):
        """Peek: retorna o caractere atual sem avançar."""
        if self.pos < len(self.source):
            return self.source[self.pos]
        return None

    def _peek_next(self):
        """Lookahead de 1: retorna o próximo caractere sem avançar."""
        idx = self.pos + 1
        if idx < len(self.source):
            return self.source[idx]
        return None

    def _advance(self):
        """
        Consome o caractere atual e atualiza contadores de linha/coluna.
        Retorna o caractere consumido.
        """
        ch = self.source[self.pos]
        self.pos    += 1
        if ch == '\n':
            self.line  += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    # -----------------------------------------------------------------------
    # Ponto de entrada — estado START do AFD
    # -----------------------------------------------------------------------

    def tokenize(self):
        """
        Percorre todo o source e retorna a lista de tokens.
        Implementa o estado START: classifica o primeiro caractere
        e faz a transição para o estado correto.
        """
        while self._current() is not None:
            tok_line = self.line
            tok_col  = self.column
            ch = self._current()

            # Transição: espaço em branco → ignora, volta ao START
            if _eh_espaco(ch):
                self._advance()
                continue

            # Transição: '/' seguido de '/' → comentário de linha
            if ch == '/' and self._peek_next() == '/':
                self._skip_line_comment()
                continue

            # Transição: '/' seguido de '*' → comentário de bloco
            if ch == '/' and self._peek_next() == '*':
                self._skip_block_comment()
                continue

            # Transição: dígito → estado NUM
            if _eh_digito(ch):
                self.tokens.append(self._read_integer(tok_line, tok_col))
                continue

            # Transição: '"' → estado STR
            if ch == '"':
                self.tokens.append(self._read_string(tok_line, tok_col))
                continue

            # Transição: letra ou '_' → estado IDENT
            if _eh_letra(ch) or ch == '_':
                self.tokens.append(self._read_identifier(tok_line, tok_col))
                continue

            # Transição: qualquer outro → estado OP
            tok = self._read_operator(tok_line, tok_col)
            if tok is not None:
                self.tokens.append(tok)

        # Token sentinela de fim de arquivo
        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return self.tokens

    # -----------------------------------------------------------------------
    # Estado COMM_LINE: consome comentário de linha // até \n
    # -----------------------------------------------------------------------
    def _skip_line_comment(self):
        while self._current() is not None and self._current() != '\n':
            self._advance()

    # -----------------------------------------------------------------------
    # Estado COMM_BLOC: consome comentário de bloco /* ... */
    # -----------------------------------------------------------------------
    def _skip_block_comment(self):
        start_line = self.line
        start_col  = self.column
        self._advance()   # consome '/'
        self._advance()   # consome '*'
        while self._current() is not None:
            if self._current() == '*' and self._peek_next() == '/':
                self._advance()   # consome '*'
                self._advance()   # consome '/'
                return
            self._advance()
        raise LexerError(
            "Comentario de bloco nao fechado (aberto em L%d:C%d)" % (start_line, start_col),
            self.line, self.column
        )

    # -----------------------------------------------------------------------
    # Estado NUM: consome [0-9]+
    # AFD: q_num -[0-9]-> q_num (loop) -[^0-9]-> aceito
    # -----------------------------------------------------------------------
    def _read_integer(self, line, col):
        buf = []
        while _eh_digito(self._current()):
            buf.append(self._advance())
        # Converte string de dígitos para inteiro manualmente
        valor = 0
        for d in buf:
            valor = valor * 10 + (ord(d) - ord('0'))
        return Token(TokenType.INTEGER, valor, line, col)

    # -----------------------------------------------------------------------
    # Estado STR: consome '"' [^"]* '"' com suporte a escapes
    # -----------------------------------------------------------------------
    def _read_string(self, line, col):
        self._advance()   # consome '"' de abertura
        buf = []
        while True:
            ch = self._current()
            if ch is None:
                raise LexerError("String literal nao fechada", line, col)
            if ch == '"':
                self._advance()   # consome '"' de fechamento
                break
            if ch == '\\':
                self._advance()   # consome '\'
                esc = self._advance()
                if   esc == 'n':  buf.append('\n')
                elif esc == 't':  buf.append('\t')
                elif esc == '\\': buf.append('\\')
                elif esc == '"':  buf.append('"')
                else:             buf.append(esc)
            else:
                buf.append(self._advance())
        # Concatena lista de chars manualmente
        resultado = ""
        for c in buf:
            resultado = resultado + c
        return Token(TokenType.STRING, resultado, line, col)

    # -----------------------------------------------------------------------
    # Estado IDENT: consome [a-zA-Z_][a-zA-Z0-9_]*
    # Após consumir, verifica na tabela de palavras reservadas.
    # -----------------------------------------------------------------------
    def _read_identifier(self, line, col):
        buf = []
        while _eh_alfanum(self._current()):
            buf.append(self._advance())
        # Monta lexema
        lexema = ""
        for c in buf:
            lexema = lexema + c
        # Verifica se é palavra reservada
        ttype = KEYWORDS.get(lexema, TokenType.IDENTIFIER)
        # Valor semântico
        if ttype == TokenType.TRUE:
            valor = True
        elif ttype == TokenType.FALSE:
            valor = False
        else:
            valor = lexema
        return Token(ttype, valor, line, col)

    # -----------------------------------------------------------------------
    # Estado OP: operadores de 1 ou 2 caracteres
    # Usa lookahead para distinguir = de ==, ! de !=, < de <=, etc.
    # -----------------------------------------------------------------------
    def _read_operator(self, line, col):
        ch   = self._advance()
        nxt  = self._current()

        # Operadores de dois caracteres (lookahead = 1)
        if ch == '=' and nxt == '=': self._advance(); return Token(TokenType.EQUAL,      '==', line, col)
        if ch == '!' and nxt == '=': self._advance(); return Token(TokenType.NOT_EQUAL,  '!=', line, col)
        if ch == '<' and nxt == '=': self._advance(); return Token(TokenType.LESS_EQ,    '<=', line, col)
        if ch == '>' and nxt == '=': self._advance(); return Token(TokenType.GREATER_EQ, '>=', line, col)
        if ch == '&' and nxt == '&': self._advance(); return Token(TokenType.AND,        '&&', line, col)
        if ch == '|' and nxt == '|': self._advance(); return Token(TokenType.OR,         '||', line, col)

        # Operadores de um caractere
        if ch == '+': return Token(TokenType.PLUS,      '+', line, col)
        if ch == '-': return Token(TokenType.MINUS,     '-', line, col)
        if ch == '*': return Token(TokenType.MULTIPLY,  '*', line, col)
        if ch == '/': return Token(TokenType.DIVIDE,    '/', line, col)
        if ch == '<': return Token(TokenType.LESS,      '<', line, col)
        if ch == '>': return Token(TokenType.GREATER,   '>', line, col)
        if ch == '=': return Token(TokenType.ASSIGN,    '=', line, col)
        if ch == '!': return Token(TokenType.NOT,       '!', line, col)
        if ch == '(': return Token(TokenType.LPAREN,    '(', line, col)
        if ch == ')': return Token(TokenType.RPAREN,    ')', line, col)
        if ch == '{': return Token(TokenType.LBRACE,    '{', line, col)
        if ch == '}': return Token(TokenType.RBRACE,    '}', line, col)
        if ch == ';': return Token(TokenType.SEMICOLON, ';', line, col)
        if ch == ',': return Token(TokenType.COMMA,     ',', line, col)

        raise LexerError("Caractere desconhecido: '%s'" % ch, line, col)

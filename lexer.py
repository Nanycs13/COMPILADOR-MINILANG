
class TokenType:
    INTEGER      = 1
    BOOLEAN      = 2
    STRING       = 3

    IDENTIFIER   = 4

    INT          = 10
    BOOL         = 11
    IF           = 12
    ELSE         = 13
    WHILE        = 14
    PRINT        = 15
    READ         = 16
    TRUE         = 17
    FALSE        = 18

    PLUS         = 20
    MINUS        = 21
    MULTIPLY     = 22
    DIVIDE       = 23

    EQUAL        = 30   
    NOT_EQUAL    = 31   
    LESS         = 32   
    GREATER      = 33   
    LESS_EQ      = 34   
    GREATER_EQ   = 35   

    AND          = 36   
    OR           = 37   
    NOT          = 38   

   
    ASSIGN       = 40   

    
    LPAREN       = 50   
    RPAREN       = 51   
    LBRACE       = 52   
    RBRACE       = 53   
    SEMICOLON    = 54   
    COMMA        = 55   

    
    EOF          = 99

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


class Token:
    def __init__(self, ttype, value, line, column):
        self.type   = ttype   
        self.value  = value    
        self.line   = line
        self.column = column

    def __repr__(self):
        return "Token(%s, %r, L%d:C%d)" % (
            TokenType.name(self.type), self.value, self.line, self.column
        )


class LexerError(Exception):
    def __init__(self, msg, line, column):
        full = "[Erro Lexico] L%d:C%d -- %s" % (line, column, msg)
        Exception.__init__(self, full)
        self.line   = line
        self.column = column



def _eh_digito(ch):
    return ch is not None and '0' <= ch <= '9'

def _eh_letra(ch):
    if ch is None:
        return False
    return ('a' <= ch <= 'z') or ('A' <= ch <= 'Z')

def _eh_alfanum(ch):
    return _eh_letra(ch) or _eh_digito(ch) or ch == '_'

def _eh_espaco(ch):
    return ch in (' ', '\t', '\n', '\r', '\f', '\v')


class Lexer:

    def __init__(self, source):
        self.source  = source       
        self.pos     = 0            
        self.line    = 1           
        self.column  = 1             
        self.tokens  = []           


    def _current(self):
        if self.pos < len(self.source):
            return self.source[self.pos]
        return None

    def _peek_next(self):
        idx = self.pos + 1
        if idx < len(self.source):
            return self.source[idx]
        return None

    def _advance(self):
        ch = self.source[self.pos]
        self.pos    += 1
        if ch == '\n':
            self.line  += 1
            self.column = 1
        else:
            self.column += 1
        return ch


    def tokenize(self):
        while self._current() is not None:
            tok_line = self.line
            tok_col  = self.column
            ch = self._current()

            if _eh_espaco(ch):
                self._advance()
                continue

            if ch == '/' and self._peek_next() == '/':
                self._skip_line_comment()
                continue

            if ch == '/' and self._peek_next() == '*':
                self._skip_block_comment()
                continue

            if _eh_digito(ch):
                self.tokens.append(self._read_integer(tok_line, tok_col))
                continue

            if ch == '"':
                self.tokens.append(self._read_string(tok_line, tok_col))
                continue

            if _eh_letra(ch) or ch == '_':
                self.tokens.append(self._read_identifier(tok_line, tok_col))
                continue

            tok = self._read_operator(tok_line, tok_col)
            if tok is not None:
                self.tokens.append(tok)

        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return self.tokens

    def _skip_line_comment(self):
        while self._current() is not None and self._current() != '\n':
            self._advance()

    def _skip_block_comment(self):
        start_line = self.line
        start_col  = self.column
        self._advance()   
        self._advance()   
        while self._current() is not None:
            if self._current() == '*' and self._peek_next() == '/':
                self._advance()   
                self._advance()   
                return
            self._advance()
        raise LexerError(
            "Comentario de bloco nao fechado (aberto em L%d:C%d)" % (start_line, start_col),
            self.line, self.column
        )

    def _read_integer(self, line, col):
        buf = []
        while _eh_digito(self._current()):
            buf.append(self._advance())
        valor = 0
        for d in buf:
            valor = valor * 10 + (ord(d) - ord('0'))
        return Token(TokenType.INTEGER, valor, line, col)

    def _read_string(self, line, col):
        self._advance()   
        buf = []
        while True:
            ch = self._current()
            if ch is None:
                raise LexerError("String literal nao fechada", line, col)
            if ch == '"':
                self._advance()   
                break
            if ch == '\\':
                self._advance()   
                esc = self._advance()
                if   esc == 'n':  buf.append('\n')
                elif esc == 't':  buf.append('\t')
                elif esc == '\\': buf.append('\\')
                elif esc == '"':  buf.append('"')
                else:             buf.append(esc)
            else:
                buf.append(self._advance())
        resultado = ""
        for c in buf:
            resultado = resultado + c
        return Token(TokenType.STRING, resultado, line, col)

    def _read_identifier(self, line, col):
        buf = []
        while _eh_alfanum(self._current()):
            buf.append(self._advance())
        
        lexema = ""
        for c in buf:
            lexema = lexema + c
        ttype = KEYWORDS.get(lexema, TokenType.IDENTIFIER)
        if ttype == TokenType.TRUE:
            valor = True
        elif ttype == TokenType.FALSE:
            valor = False
        else:
            valor = lexema
        return Token(ttype, valor, line, col)

    def _read_operator(self, line, col):
        ch   = self._advance()
        nxt  = self._current()

        if ch == '=' and nxt == '=': self._advance(); return Token(TokenType.EQUAL,      '==', line, col)
        if ch == '!' and nxt == '=': self._advance(); return Token(TokenType.NOT_EQUAL,  '!=', line, col)
        if ch == '<' and nxt == '=': self._advance(); return Token(TokenType.LESS_EQ,    '<=', line, col)
        if ch == '>' and nxt == '=': self._advance(); return Token(TokenType.GREATER_EQ, '>=', line, col)
        if ch == '&' and nxt == '&': self._advance(); return Token(TokenType.AND,        '&&', line, col)
        if ch == '|' and nxt == '|': self._advance(); return Token(TokenType.OR,         '||', line, col)

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

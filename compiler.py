

import sys
import os

from lexer        import Lexer,            LexerError
from parser       import Parser,           ParseError
from semantic     import SemanticAnalyzer, SemanticError
from ir_generator import IRGenerator
from codegen      import TACInterpreter,   X86Generator



BANNER = """
+------------------------------------------+
|   MiniLang Compiler  v1.0                |
|   Projeto de Compiladores -- 2025        |
+------------------------------------------+
"""

def _secao(titulo):
    separador = "-" * 50
    print("")
    print(separador)
    print("  " + titulo)
    print(separador)

def _ok(msg):
    print("  [OK]  " + msg)

def _falha(msg):
    print("  [ERRO] " + msg, file=sys.stderr)



class Argumentos:
    

    def __init__(self):
        self.arquivo  = None    
        self.tokens   = False   
        self.ir       = False   
        self.asm      = False   
        self.verbose  = False   
        self.entrada  = ""      

def _parse_args(argv):
   
    args = Argumentos()

    if len(argv) < 2:
        print("Uso: python compiler.py <arquivo.mini> [opcoes]")
        print("  --tokens    Exibe a lista de tokens gerados")
        print("  --ir        Exibe o codigo intermediario (TAC)")
        print("  --asm       Gera Assembly x86 em <arquivo.s>")
        print("  --input N   Valores para read(), separados por virgula")
        print("  -v          Modo detalhado")
        sys.exit(0)

    i = 1
    while i < len(argv):
        arg = argv[i]

        if arg == "--tokens":
            args.tokens = True
        elif arg == "--ir":
            args.ir = True
        elif arg == "--asm":
            args.asm = True
        elif arg == "-v" or arg == "--verbose":
            args.verbose = True
        elif arg == "--input":
            if i + 1 < len(argv):
                i += 1
                args.entrada = argv[i]
            else:
                print("Erro: --input requer um valor.")
                sys.exit(1)
        elif arg[0] == '-':
            print("Opcao desconhecida: " + arg)
            sys.exit(1)
        else:
            # Argumento posicional = arquivo
            args.arquivo = arg

        i += 1

    if args.arquivo is None:
        print("Erro: nenhum arquivo especificado.")
        sys.exit(1)

    return args



def compilar(fonte, nome_arquivo, args):
  

   
    _secao("FASE 1 -- Analise Lexica (Scanner / AFD)")
    try:
        lexer  = Lexer(fonte)
        tokens = lexer.tokenize()
        _ok("%d tokens gerados." % len(tokens))
    except LexerError as e:
        _falha(str(e))
        return False

    if args.tokens or args.verbose:
        print("")
        for tok in tokens:
            print("    " + str(tok))

   
    _secao("FASE 2 -- Analise Sintatica (Parser Descendente Recursivo)")
    try:
        parser = Parser(tokens)
        ast    = parser.parse()
        _ok("AST construida com sucesso.")
    except ParseError as e:
        _falha(str(e))
        return False

   
    _secao("FASE 3 -- Analise Semantica (Tabela de Simbolos + Type Checking)")
    try:
        analisador = SemanticAnalyzer()
        simbolos   = analisador.analisar(ast)
        _ok("Sem erros semanticos.")
        print("")
        print("  Tabela de Simbolos:")
        print(simbolos.dump())
    except SemanticError as e:
        _falha(str(e))
        return False

    
    _secao("FASE 4 -- Geracao de Codigo Intermediario (TAC)")
    gerador = IRGenerator()
    ir      = gerador.gerar(ast)
    _ok("%d instrucoes TAC geradas." % len(ir))

    if args.ir or args.verbose:
        print("")
        print("  Codigo TAC:")
        print("")
        print(gerador.codigo_str())

    
    _secao("FASE 5 -- Geracao de Codigo Final")

    if args.asm:
        
        x86_gen = X86Generator(ir)
        asm     = x86_gen.gerar()
       
        base = nome_arquivo
        if '.' in base:
            
            idx = len(base) - 1
            while idx >= 0 and base[idx] != '.':
                idx -= 1
            if idx >= 0:
                base = base[:idx]
        saida_asm = base + ".s"
        f = open(saida_asm, 'w', encoding='utf-8')
        f.write(asm)
        f.close()
        _ok("Assembly x86 salvo em: " + saida_asm)
        if args.verbose:
            print("")
            print(asm)
    else:
        
        entradas = []
        if args.entrada != "":
           
            partes = []
            atual  = ""
            for ch in args.entrada:
                if ch == ',':
                    if atual != "":
                        partes.append(atual)
                    atual = ""
                else:
                    atual = atual + ch
            if atual != "":
                partes.append(atual)
            for p in partes:
                entradas.append(int(p))

        interprete = TACInterpreter(ir)
        saida      = interprete.executar(entradas)

        _ok("Execucao concluida via interprete TAC.")

        if len(saida) > 0:
            print("")
            print("  --- Saida do Programa ---")
            for linha in saida:
                print("  " + linha)

    return True



def main():
    print(BANNER)

    args = _parse_args(sys.argv)

    if not os.path.exists(args.arquivo):
        _falha("Arquivo nao encontrado: " + args.arquivo)
        sys.exit(1)

    
    f      = open(args.arquivo, 'r', encoding='utf-8')
    fonte  = f.read()
    f.close()

    print("  Arquivo: %s (%d caracteres)" % (args.arquivo, len(fonte)))

    sucesso = compilar(fonte, args.arquivo, args)

    _secao("RESULTADO FINAL")
    if sucesso:
        _ok("Compilacao concluida com sucesso!")
    else:
        _falha("Compilacao falhou.")
        sys.exit(1)


if __name__ == "__main__":
    main()

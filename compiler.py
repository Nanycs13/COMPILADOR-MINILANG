"""
=============================================================================
COMPILADOR MINILANG — Ponto de Entrada Principal
=============================================================================
Executa todas as fases de compilação em sequência:
  1. Análise Léxica  (Lexer)
  2. Análise Sintática (Parser)
  3. Análise Semântica (SemanticAnalyzer)
  4. Geração de Código Intermediário (IRGenerator)
  5. Geração de Código Final (X86Generator / TACInterpreter)

Uso:
  python compiler.py <arquivo.mini>            # compila e executa (interpreta TAC)
  python compiler.py <arquivo.mini> --asm      # gera assembly x86 em <arquivo.s>
  python compiler.py <arquivo.mini> --tokens   # exibe tokens (modo debug)
  python compiler.py <arquivo.mini> --ir       # exibe código intermediário
=============================================================================
"""

import sys
import os
import argparse
from lexer      import Lexer, LexerError
from parser     import Parser, ParseError
from semantic   import SemanticAnalyzer, SemanticError
from ir_generator import IRGenerator
from codegen    import TACInterpreter, X86Generator


# ---------------------------------------------------------------------------
# Banner e utilitários de saída
# ---------------------------------------------------------------------------
BANNER = """
╔══════════════════════════════════════════╗
║   MiniLang Compiler  v1.0               ║
║   Projeto de Compiladores — 2025        ║
╚══════════════════════════════════════════╝
"""

def section(title: str):
    print(f"\n{'─'*50}")
    print(f"  {title}")
    print(f"{'─'*50}")

def ok(msg: str):
    print(f"  ✓  {msg}")

def fail(msg: str):
    print(f"  ✗  {msg}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Pipeline de compilação
# ---------------------------------------------------------------------------
def compile_source(source: str, filename: str, args) -> bool:
    """
    Executa o pipeline completo. Retorna True se bem-sucedido.
    """

    # ── FASE 1: Análise Léxica ───────────────────────────────────────────
    section("FASE 1 — Análise Léxica (Scanner)")
    try:
        lexer  = Lexer(source)
        tokens = lexer.tokenize()
        ok(f"{len(tokens)} tokens gerados.")
    except LexerError as e:
        fail(str(e))
        return False

    if args.tokens:
        print()
        for tok in tokens:
            print(f"    {tok}")

    # ── FASE 2: Análise Sintática ────────────────────────────────────────
    section("FASE 2 — Análise Sintática (Parser)")
    try:
        parser = Parser(tokens)
        ast    = parser.parse()
        ok("AST construída com sucesso.")
    except ParseError as e:
        fail(str(e))
        return False

    # ── FASE 3: Análise Semântica ────────────────────────────────────────
    section("FASE 3 — Análise Semântica")
    try:
        analyzer = SemanticAnalyzer()
        symbols  = analyzer.analyze(ast)
        ok("Sem erros semânticos.")
        print(f"\n  Tabela de Símbolos:")
        print(symbols.dump())
    except SemanticError as e:
        fail(str(e))
        return False

    # ── FASE 4: Geração de Código Intermediário ──────────────────────────
    section("FASE 4 — Geração de Código Intermediário (TAC)")
    ir_gen = IRGenerator()
    ir     = ir_gen.generate(ast)
    ok(f"{len(ir)} instruções TAC geradas.")

    if args.ir or args.verbose:
        print(f"\n  Código Intermediário (TAC):\n")
        print(ir_gen.code_str())

    # ── FASE 5: Saída final ──────────────────────────────────────────────
    section("FASE 5 — Geração de Código Final")

    if args.asm:
        # Gera Assembly x86
        x86    = X86Generator(ir)
        asm    = x86.generate()
        out    = filename.rsplit('.', 1)[0] + '.s'
        with open(out, 'w') as f:
            f.write(asm)
        ok(f"Assembly x86 salvo em: {out}")
        if args.verbose:
            print(f"\n{asm}")
    else:
        # Interpreta o TAC diretamente
        inputs = [int(x) for x in args.input.split(',')] if args.input else []
        interp = TACInterpreter(ir)
        output = interp.run(inputs)
        ok("Execução concluída via intérprete TAC.")
        if output:
            print(f"\n  ─── Saída do Programa ───")
            for line in output:
                print(f"  {line}")

    return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    print(BANNER)

    ap = argparse.ArgumentParser(
        description="Compilador MiniLang — todas as fases"
    )
    ap.add_argument("file",          help="Arquivo fonte (.mini)")
    ap.add_argument("--tokens",      action="store_true", help="Exibe lista de tokens")
    ap.add_argument("--ir",          action="store_true", help="Exibe código TAC")
    ap.add_argument("--asm",         action="store_true", help="Gera Assembly x86 (.s)")
    ap.add_argument("--verbose","-v",action="store_true", help="Modo detalhado")
    ap.add_argument("--input",       default="",          help="Entradas para read(), separadas por vírgula")
    args = ap.parse_args()

    if not os.path.exists(args.file):
        fail(f"Arquivo não encontrado: {args.file}")
        sys.exit(1)

    with open(args.file, 'r', encoding='utf-8') as f:
        source = f.read()

    print(f"  Arquivo: {args.file} ({len(source)} caracteres)\n")

    success = compile_source(source, args.file, args)
    section("RESULTADO")
    if success:
        ok("Compilação concluída com sucesso!")
    else:
        fail("Compilação falhou.")
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
=============================================================================
ANÁLISE SEMÂNTICA — Compilador MiniLang
=============================================================================
IMPLEMENTAÇÃO MANUAL — sem typing, sem dataclasses, sem collections

Estruturas de dados implementadas do zero:
  - PilhaEscopos: pilha de dicionários (lista de listas de pares chave/valor)
  - Tabela de Símbolos: busca dos escopos mais internos aos mais externos
  - Lista de erros: acumulada durante a travessia, lançada ao final
=============================================================================
"""

from ast_nodes import (
    Program, Block, VarDecl, Assignment, IfStmt, WhileStmt,
    PrintStmt, ReadStmt, BinaryOp, UnaryOp,
    IntLiteral, BoolLiteral, StringLiteral, Identifier, Visitor
)


# ---------------------------------------------------------------------------
# Erro Semântico
# ---------------------------------------------------------------------------
class SemanticError(Exception):
    def __init__(self, msg, line=0):
        full = "[Erro Semantico] L%d -- %s" % (line, msg)
        Exception.__init__(self, full)
        self.line = line


# ---------------------------------------------------------------------------
# Dicionário simples implementado como lista de pares (chave, valor)
# (sem usar dict do Python não é viável — dict é estrutura nativa da linguagem,
#  não uma biblioteca. Aqui implementamos um dicionário manual para os escopos.)
# ---------------------------------------------------------------------------
class DictManual:
    """
    Dicionário implementado como lista de pares [chave, valor].
    Operações O(n) — suficiente para o tamanho de programas didáticos.
    """
    def __init__(self):
        self._pares = []   # lista de [chave, valor]

    def set(self, chave, valor):
        """Insere ou atualiza a chave."""
        for par in self._pares:
            if par[0] == chave:
                par[1] = valor
                return
        self._pares.append([chave, valor])

    def get(self, chave):
        """Retorna o valor ou None se não encontrado."""
        for par in self._pares:
            if par[0] == chave:
                return par[1]
        return None

    def contem(self, chave):
        """Retorna True se a chave existe."""
        for par in self._pares:
            if par[0] == chave:
                return True
        return False

    def itens(self):
        """Retorna lista de [chave, valor]."""
        return self._pares

    def tamanho(self):
        return len(self._pares)


# ---------------------------------------------------------------------------
# Tabela de Símbolos com escopos aninhados (pilha de DictManual)
# ---------------------------------------------------------------------------
class TabelaDeSimbolos:
    """
    Pilha de escopos implementada como lista de DictManual.
    - enter_scope(): empilha novo escopo
    - exit_scope(): desempilha
    - declarar(): insere no escopo do topo
    - buscar(): percorre do topo à base (mais interno → mais externo)
    """

    def __init__(self):
        # Começa com o escopo global
        self._escopos = [DictManual()]

    def enter_scope(self):
        """Abre um novo escopo (empilha)."""
        self._escopos.append(DictManual())

    def exit_scope(self):
        """Fecha o escopo atual (desempilha). Nunca remove o global."""
        if len(self._escopos) > 1:
            self._escopos.pop()

    def declarar(self, nome, tipo, linha):
        """
        Declara variável no escopo atual.
        Lança SemanticError se já declarada neste mesmo escopo.
        """
        topo = self._escopos[len(self._escopos) - 1]
        if topo.contem(nome):
            raise SemanticError(
                "Variavel '%s' ja declarada neste escopo." % nome,
                linha
            )
        topo.set(nome, tipo)

    def buscar(self, nome):
        """
        Busca do escopo mais interno ao mais externo.
        Retorna o tipo (string) ou None se não encontrado.
        """
        # Percorre de trás para frente (do topo da pilha à base)
        i = len(self._escopos) - 1
        while i >= 0:
            tipo = self._escopos[i].get(nome)
            if tipo is not None:
                return tipo
            i -= 1
        return None

    def buscar_ou_erro(self, nome, linha):
        """Busca variável; lança SemanticError se não encontrada."""
        tipo = self.buscar(nome)
        if tipo is None:
            raise SemanticError(
                "Variavel '%s' nao declarada." % nome,
                linha
            )
        return tipo

    def dump(self):
        """Representação textual para relatório."""
        linhas = []
        for i in range(len(self._escopos)):
            if i == 0:
                rotulo = "global"
            else:
                rotulo = "escopo %d" % i
            for par in self._escopos[i].itens():
                linhas.append("  [%s] %s: %s" % (rotulo, par[0], par[1]))
        if len(linhas) == 0:
            return "  (vazia)"
        # Concatena com quebra de linha manualmente
        resultado = linhas[0]
        for j in range(1, len(linhas)):
            resultado = resultado + "\n" + linhas[j]
        return resultado


# ---------------------------------------------------------------------------
# Analisador Semântico — Visitor sobre a AST
# ---------------------------------------------------------------------------
class SemanticAnalyzer(Visitor):
    """
    Percorre a AST usando o Visitor Pattern.
    - Gerencia a TabelaDeSimbolos com escopos.
    - Acumula erros em self.erros (lista de strings).
    - Lança SemanticError ao final se houver erros.
    - Cada visit_Expressao retorna o tipo da expressão (string).
    """

    # Grupos de operadores para type checking
    OPS_ARITM  = ('+', '-', '*', '/')
    OPS_RELAC  = ('<', '>', '<=', '>=')
    OPS_IGUAL  = ('==', '!=')
    OPS_LOGICO = ('&&', '||')

    def __init__(self):
        self.simbolos = TabelaDeSimbolos()
        self.erros    = []   # lista de strings de erro

    def analisar(self, arvore):
        """Ponto de entrada: visita o nó raiz e valida."""
        arvore.accept(self)
        if len(self.erros) > 0:
            # Monta mensagem com todos os erros acumulados
            msg = "Erros semanticos encontrados:\n"
            for e in self.erros:
                msg = msg + e + "\n"
            raise SemanticError(msg, 0)
        return self.simbolos

    def _registrar_erro(self, msg, linha=0):
        self.erros.append("  L%d: %s" % (linha, msg))

    # -----------------------------------------------------------------------
    # Visitores de instrução
    # -----------------------------------------------------------------------

    def visit_Program(self, node):
        for stmt in node.stmts:
            stmt.accept(self)

    def visit_Block(self, node):
        self.simbolos.enter_scope()
        for stmt in node.stmts:
            stmt.accept(self)
        self.simbolos.exit_scope()

    def visit_VarDecl(self, node):
        if node.var_type != "int" and node.var_type != "bool":
            self._registrar_erro(
                "Tipo desconhecido: '%s'." % node.var_type,
                node.line
            )
            return

        if node.init is not None:
            tipo_init = node.init.accept(self)
            if tipo_init is not None and tipo_init != node.var_type:
                self._registrar_erro(
                    "Atribuicao invalida: '%s %s' nao pode receber valor do tipo '%s'."
                    % (node.var_type, node.name, tipo_init),
                    node.line
                )

        try:
            self.simbolos.declarar(node.name, node.var_type, node.line)
        except SemanticError as e:
            self._registrar_erro(str(e), node.line)

    def visit_Assignment(self, node):
        try:
            tipo_var = self.simbolos.buscar_ou_erro(node.name, node.line)
            tipo_val = node.value.accept(self)
            if tipo_val is not None and tipo_val != tipo_var:
                self._registrar_erro(
                    "Atribuicao de tipo incompativel: '%s' e '%s', mas valor e '%s'."
                    % (node.name, tipo_var, tipo_val),
                    node.line
                )
        except SemanticError as e:
            self._registrar_erro(str(e), node.line)

    def visit_IfStmt(self, node):
        tipo_cond = node.condition.accept(self)
        if tipo_cond is not None and tipo_cond != "bool":
            self._registrar_erro(
                "Condicao do 'if' deve ser booleana, obtido '%s'." % tipo_cond,
                node.line
            )
        node.then_body.accept(self)
        if node.else_body is not None:
            node.else_body.accept(self)

    def visit_WhileStmt(self, node):
        tipo_cond = node.condition.accept(self)
        if tipo_cond is not None and tipo_cond != "bool":
            self._registrar_erro(
                "Condicao do 'while' deve ser booleana, obtido '%s'." % tipo_cond,
                node.line
            )
        node.body.accept(self)

    def visit_PrintStmt(self, node):
        node.value.accept(self)   # aceita qualquer tipo

    def visit_ReadStmt(self, node):
        try:
            tipo_var = self.simbolos.buscar_ou_erro(node.name, node.line)
            if tipo_var != "int":
                self._registrar_erro(
                    "'read' suporta apenas variaveis 'int', mas '%s' e '%s'."
                    % (node.name, tipo_var),
                    node.line
                )
        except SemanticError as e:
            self._registrar_erro(str(e), node.line)

    # -----------------------------------------------------------------------
    # Visitores de expressão — retornam o tipo (string) da expressão
    # -----------------------------------------------------------------------

    def visit_IntLiteral(self, node):
        return "int"

    def visit_BoolLiteral(self, node):
        return "bool"

    def visit_StringLiteral(self, node):
        return "string"

    def visit_Identifier(self, node):
        try:
            return self.simbolos.buscar_ou_erro(node.name, node.line)
        except SemanticError as e:
            self._registrar_erro(str(e), node.line)
            return None

    def visit_UnaryOp(self, node):
        tipo_op = node.operand.accept(self)
        if node.op == '!':
            if tipo_op is not None and tipo_op != "bool":
                self._registrar_erro(
                    "'!' requer operando booleano, obtido '%s'." % tipo_op,
                    node.line
                )
            return "bool"
        if node.op == '-':
            if tipo_op is not None and tipo_op != "int":
                self._registrar_erro(
                    "Negacao unaria requer inteiro, obtido '%s'." % tipo_op,
                    node.line
                )
            return "int"
        return tipo_op

    def visit_BinaryOp(self, node):
        tipo_esq = node.left.accept(self)
        tipo_dir = node.right.accept(self)
        op       = node.op

        # Operadores aritméticos: exigem int, produzem int
        for op_aritm in self.OPS_ARITM:
            if op == op_aritm:
                if tipo_esq is not None and tipo_esq != "int":
                    self._registrar_erro(
                        "Operador '%s' requer inteiros; lado esquerdo e '%s'." % (op, tipo_esq),
                        node.line
                    )
                if tipo_dir is not None and tipo_dir != "int":
                    self._registrar_erro(
                        "Operador '%s' requer inteiros; lado direito e '%s'." % (op, tipo_dir),
                        node.line
                    )
                return "int"

        # Operadores relacionais: exigem int, produzem bool
        for op_rel in self.OPS_RELAC:
            if op == op_rel:
                if tipo_esq is not None and tipo_esq != "int":
                    self._registrar_erro(
                        "Operador '%s' compara inteiros; lado esquerdo e '%s'." % (op, tipo_esq),
                        node.line
                    )
                if tipo_dir is not None and tipo_dir != "int":
                    self._registrar_erro(
                        "Operador '%s' compara inteiros; lado direito e '%s'." % (op, tipo_dir),
                        node.line
                    )
                return "bool"

        # Operadores de igualdade: exigem mesmo tipo, produzem bool
        for op_ig in self.OPS_IGUAL:
            if op == op_ig:
                if tipo_esq is not None and tipo_dir is not None and tipo_esq != tipo_dir:
                    self._registrar_erro(
                        "Comparacao '%s' entre tipos distintos: '%s' e '%s'."
                        % (op, tipo_esq, tipo_dir),
                        node.line
                    )
                return "bool"

        # Operadores lógicos: exigem bool, produzem bool
        for op_log in self.OPS_LOGICO:
            if op == op_log:
                if tipo_esq is not None and tipo_esq != "bool":
                    self._registrar_erro(
                        "Operador '%s' requer booleanos; lado esquerdo e '%s'." % (op, tipo_esq),
                        node.line
                    )
                if tipo_dir is not None and tipo_dir != "bool":
                    self._registrar_erro(
                        "Operador '%s' requer booleanos; lado direito e '%s'." % (op, tipo_dir),
                        node.line
                    )
                return "bool"

        self._registrar_erro("Operador desconhecido: '%s'." % op, node.line)
        return None



from ast_nodes import (
    Program, Block, VarDecl, Assignment, IfStmt, WhileStmt,
    PrintStmt, ReadStmt, BinaryOp, UnaryOp,
    IntLiteral, BoolLiteral, StringLiteral, Identifier, Visitor
)



class TACInstr:

    def __init__(self, op, result=None, arg1=None, arg2=None):
        self.op     = op       
        self.result = result   
        self.arg1   = arg1     
        self.arg2   = arg2     

    def __str__(self):
        if self.op == 'label':
            return "%s:" % self.result

        if self.op == 'goto':
            return "  goto %s" % self.arg1

        if self.op == 'if_false':
            return "  if_false %s goto %s" % (self.arg1, self.arg2)

        if self.op == 'print':
            return "  print %s" % str(self.arg1)

        if self.op == 'read':
            return "  read %s" % self.result

        if self.op == 'copy':
            return "  %s = %s" % (self.result, str(self.arg1))

        if self.op == 'unary_minus':
            return "  %s = -%s" % (self.result, str(self.arg1))

        if self.op == 'unary_not':
            return "  %s = !%s" % (self.result, str(self.arg1))

        
        return "  %s = %s %s %s" % (
            self.result, str(self.arg1), self.op, str(self.arg2)
        )


class IRGenerator(Visitor):

    def __init__(self):
        self.instrucoes  = []   # lista de TACInstr
        self._temp_count  = 0
        self._label_count = 0


    def _novo_temp(self):
        nome = "t%d" % self._temp_count
        self._temp_count += 1
        return nome

    def _novo_rotulo(self):
        nome = "L%d" % self._label_count
        self._label_count += 1
        return nome

    def _emitir(self, instr):
        self.instrucoes.append(instr)

    def gerar(self, arvore):
        arvore.accept(self)
        return self.instrucoes

    def codigo_str(self):
        resultado = ""
        for i in range(len(self.instrucoes)):
            if i == 0:
                resultado = str(self.instrucoes[0])
            else:
                resultado = resultado + "\n" + str(self.instrucoes[i])
        return resultado


    def visit_Program(self, node):
        for stmt in node.stmts:
            stmt.accept(self)

    def visit_Block(self, node):
        for stmt in node.stmts:
            stmt.accept(self)

    def visit_VarDecl(self, node):
        if node.init is not None:
            src = node.init.accept(self)
            self._emitir(TACInstr('copy', node.name, src))

    def visit_Assignment(self, node):
        src = node.value.accept(self)
        self._emitir(TACInstr('copy', node.name, src))

    def visit_IfStmt(self, node):
        cond   = node.condition.accept(self)
        l_else = self._novo_rotulo()
        l_fim  = self._novo_rotulo()

        self._emitir(TACInstr('if_false', arg1=cond, arg2=l_else))
        node.then_body.accept(self)
        self._emitir(TACInstr('goto', arg1=l_fim))
        self._emitir(TACInstr('label', result=l_else))
        if node.else_body is not None:
            node.else_body.accept(self)
        self._emitir(TACInstr('label', result=l_fim))

    def visit_WhileStmt(self, node):
        l_inicio = self._novo_rotulo()
        l_fim    = self._novo_rotulo()

        self._emitir(TACInstr('label', result=l_inicio))
        cond = node.condition.accept(self)
        self._emitir(TACInstr('if_false', arg1=cond, arg2=l_fim))
        node.body.accept(self)
        self._emitir(TACInstr('goto', arg1=l_inicio))
        self._emitir(TACInstr('label', result=l_fim))

    def visit_PrintStmt(self, node):
        val = node.value.accept(self)
        self._emitir(TACInstr('print', arg1=val))

    def visit_ReadStmt(self, node):
        self._emitir(TACInstr('read', result=node.name))


    def visit_IntLiteral(self, node):
        return node.value        

    def visit_BoolLiteral(self, node):
        return node.value        

    def visit_StringLiteral(self, node):
        return '"' + node.value + '"'

    def visit_Identifier(self, node):
        return node.name         

    def visit_UnaryOp(self, node):
        operando = node.operand.accept(self)
        tmp = self._novo_temp()
        if node.op == '!':
            self._emitir(TACInstr('unary_not', result=tmp, arg1=operando))
        else:  # '-'
            self._emitir(TACInstr('unary_minus', result=tmp, arg1=operando))
        return tmp

    def visit_BinaryOp(self, node):
        esq = node.left.accept(self)
        dir = node.right.accept(self)
        tmp = self._novo_temp()
        self._emitir(TACInstr(node.op, result=tmp, arg1=esq, arg2=dir))
        return tmp

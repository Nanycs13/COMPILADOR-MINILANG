
class ASTNode:
    def accept(self, visitor):
        # Descobre o nome do método pelo tipo do nó
        nome_metodo = 'visit_' + self.__class__.__name__
        metodo = getattr(visitor, nome_metodo)
        return metodo(self)

class IntLiteral(ASTNode):
    def __init__(self, value, line=0):
        self.value = value
        self.line  = line

class BoolLiteral(ASTNode):
    def __init__(self, value, line=0):
        self.value = value
        self.line  = line

class StringLiteral(ASTNode):
    def __init__(self, value, line=0):
        self.value = value
        self.line  = line

class Identifier(ASTNode):
    def __init__(self, name, line=0):
        self.name = name
        self.line = line

class BinaryOp(ASTNode):
    def __init__(self, op, left, right, line=0):
        self.op    = op
        self.left  = left
        self.right = right
        self.line  = line

class UnaryOp(ASTNode):
    def __init__(self, op, operand, line=0):
        self.op      = op
        self.operand = operand
        self.line    = line

class VarDecl(ASTNode):
    def __init__(self, var_type, name, init, line=0):
        self.var_type = var_type   
        self.name     = name
        self.init     = init       
        self.line     = line

class Assignment(ASTNode):
    def __init__(self, name, value, line=0):
        self.name  = name
        self.value = value
        self.line  = line

class IfStmt(ASTNode):
    def __init__(self, condition, then_body, else_body, line=0):
        self.condition = condition
        self.then_body = then_body
        self.else_body = else_body   
        self.line      = line

class WhileStmt(ASTNode):
    def __init__(self, condition, body, line=0):
        self.condition = condition
        self.body      = body
        self.line      = line

class PrintStmt(ASTNode):
    def __init__(self, value, line=0):
        self.value = value
        self.line  = line

class ReadStmt(ASTNode):
    def __init__(self, name, line=0):
        self.name = name
        self.line = line

class Block(ASTNode):
    def __init__(self, stmts, line=0):
        self.stmts = stmts   
        self.line  = line

class Program(ASTNode):
    def __init__(self, stmts):
        self.stmts = stmts   

class Visitor:
    def visit_IntLiteral(self, node):    pass
    def visit_BoolLiteral(self, node):   pass
    def visit_StringLiteral(self, node): pass
    def visit_Identifier(self, node):    pass
    def visit_BinaryOp(self, node):      pass
    def visit_UnaryOp(self, node):       pass
    def visit_VarDecl(self, node):       pass
    def visit_Assignment(self, node):    pass
    def visit_IfStmt(self, node):        pass
    def visit_WhileStmt(self, node):     pass
    def visit_PrintStmt(self, node):     pass
    def visit_ReadStmt(self, node):      pass
    def visit_Block(self, node):         pass
    def visit_Program(self, node):       pass

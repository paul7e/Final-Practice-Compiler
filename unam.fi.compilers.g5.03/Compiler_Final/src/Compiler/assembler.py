from llvmlite import ir
from lark import Token

# Uso de inst32 por simplicidad y comodidad
class assemblerCode:
    def __init__(self):
        self.module = ir.Module(name="module")
        self.builder = None
        self.func = None
        self.variables = {}
        self.int32 = ir.IntType(32)

    def transform(self, ast):
        # Creacion de funcion main
        func_type = ir.FunctionType(ir.VoidType(), [])
        self.func = ir.Function(self.module, func_type, name="main")
        block = self.func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(block)

        # AST es: ('program', [lista de statements])
        for statement in ast[1]:
            self.process_statement(statement)

        # Asegurar un retorno void al final si el bloque no esta cerrado
        if not self.builder.block.is_terminated:
            self.builder.ret_void()
            
        return self.module

    def process_statement(self, stmt):
        if not isinstance(stmt, tuple):
            return

        tag = stmt[0]
        params = stmt[1]

        if tag == 'var_decl':
            self.handle_var_decl(params)
        elif tag == 'assign':
            self.handle_assign(params)
        elif tag == 'if':
            self.handle_if(params)
        elif tag == 'block':
            self.handle_block(params)
        elif tag == 'expr_stmt':
            if isinstance(params, list) and len(params) > 0:
                self.eval_expr(params[0])
            else:
                self.eval_expr(params)

    def handle_var_decl(self, items):
        identifier = None
        value_node = None
        
        for item in items:
            if isinstance(item, Token) and item.type == 'IDENTIFIER':
                identifier = item.value
            elif isinstance(item, tuple):
                value_node = item
        
        if identifier is None:
            raise ValueError("Declaración sin identificador")

        ptr = self.builder.alloca(self.int32, name=identifier)
        self.variables[identifier] = ptr

        if value_node:
            val = self.eval_expr(value_node)
            self.builder.store(val, ptr)
        else:
            self.builder.store(ir.Constant(self.int32, 0), ptr)

    def handle_assign(self, items):
        var_name = None
        expr_node = None

        for item in items:
            if isinstance(item, Token) and item.type == 'IDENTIFIER':
                var_name = item.value
            elif isinstance(item, tuple):
                expr_node = item
        
        if not var_name: 
            return # Omitirlo si esta mal formado

        val = self.eval_expr(expr_node)
        ptr = self.variables.get(var_name)
        
        if ptr is None:
            raise ValueError(f"Variable no declarada: {var_name}")
            
        self.builder.store(val, ptr)

    def handle_if(self, items):
        nodos_relevantes = [x for x in items if isinstance(x, tuple)]
        
        if not nodos_relevantes: return

        cond_node = nodos_relevantes[0]
        then_node = nodos_relevantes[1]
        else_node = nodos_relevantes[2] if len(nodos_relevantes) > 2 else None

        # Evaluar condicion
        cond_val_i32 = self.eval_expr(cond_node)
        
        # Convertir a booleano (i1) comparando con 0
        cond_val = self.builder.icmp_signed('!=', cond_val_i32, ir.Constant(self.int32, 0), name="ifcond")

        func = self.func
        then_bb = func.append_basic_block(name="then")
        else_bb = func.append_basic_block(name="else") if else_node else None
        merge_bb = func.append_basic_block(name="merge")

        if else_bb:
            self.builder.cbranch(cond_val, then_bb, else_bb)
        else:
            self.builder.cbranch(cond_val, then_bb, merge_bb)

        # THEN
        self.builder.position_at_start(then_bb)
        self.process_statement(then_node)
        if not self.builder.block.is_terminated:
            self.builder.branch(merge_bb)

        # ELSE
        if else_bb:
            self.builder.position_at_start(else_bb)
            self.process_statement(else_node)
            if not self.builder.block.is_terminated:
                self.builder.branch(merge_bb)

        self.builder.position_at_start(merge_bb)

    def handle_block(self, statements):
        for stmt in statements:
            self.process_statement(stmt)

    def eval_expr(self, expr):
        # Caso base: tokens directos
        if isinstance(expr, Token):
            if expr.type == 'IDENTIFIER':
                ptr = self.variables.get(expr.value)
                if not ptr: raise ValueError(f"Var desconocida {expr.value}")
                return self.builder.load(ptr, name=expr.value)
            elif expr.type == 'NUMBER':
                return ir.Constant(self.int32, int(expr.value))

        if not isinstance(expr, tuple):
            raise ValueError(f"Expresión desconocida: {expr}")

        tag = expr[0]
        content = expr[1]

        if tag == 'const':
            return ir.Constant(self.int32, int(content))
        
        elif tag == 'var':
            ptr = self.variables.get(content)
            if ptr is None:
                raise ValueError(f"Variable no declarada: {content}")
            return self.builder.load(ptr, name=content)
            
        elif tag == 'arith':
            left_val = self.eval_expr(content[0])
            right_val = self.eval_expr(content[2])
            op = content[1].value
            
            if op == '+': return self.builder.add(left_val, right_val, name="add")
            elif op == '-': return self.builder.sub(left_val, right_val, name="sub")
            elif op == '*': return self.builder.mul(left_val, right_val, name="mul")
            elif op == '/': return self.builder.sdiv(left_val, right_val, name="div")
            
        elif tag == 'compare':
            left_val = self.eval_expr(content[0])
            right_val = self.eval_expr(content[2])
            op = content[1].value
            
            # Transpaso del operador directamente (>, <, ==)
            # llvmlite lo convierte internamente
            res_i1 = self.builder.icmp_signed(op, left_val, right_val, name="cmp")
            
            # Extencion del resultado de 1 bit a 32 bits para poder asignarlo a variables
            return self.builder.zext(res_i1, self.int32, name="bool_to_int")
                
        elif tag == 'parentheses':
            for item in content:
                if isinstance(item, tuple):
                    return self.eval_expr(item)
                    
        raise ValueError(f"Operación no soportada: {tag}")
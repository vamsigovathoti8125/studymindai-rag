import ast


class SafeEval(ast.NodeVisitor):
    """Safely evaluate arithmetic expressions using AST."""

    allowed_nodes = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Num, ast.Constant,
                     ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod,
                     ast.USub, ast.UAdd, ast.FloorDiv, ast.LShift, ast.RShift)

    def visit(self, node):
        if not isinstance(node, self.allowed_nodes):
            raise ValueError(f"Disallowed expression: {type(node).__name__}")
        return super().visit(node)

    def eval(self, expr: str):
        node = ast.parse(expr, mode="eval")
        self.visit(node)
        return eval(compile(node, filename="", mode="eval"))


def calculate(expr: str):
    se = SafeEval()
    return se.eval(expr)

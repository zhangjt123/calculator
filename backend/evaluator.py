"""安全的高精度算术表达式求值器。

支持：
- 四则运算 + - * /、乘方 **、一元正负号、括号
- 函数：sqrt sin cos tan asin acos atan ln log exp factorial abs
- 常量：pi e
安全：字符白名单 + AST 节点/函数白名单；表达式长度 200、AST 深度 32。
高精度：Decimal 50 位有效数字；三角/对数等超越函数用 math 浮点实现（约 15 位）。
三角函数按角度制（度）。
"""
from __future__ import annotations

import ast
import math
from decimal import Decimal, DivisionByZero, InvalidOperation, getcontext

getcontext().prec = 50

MAX_LENGTH = 200
MAX_DEPTH = 32

_ALLOWED_CHARS = frozenset(
    "0123456789.+-*/() \t" + "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
)
_ALLOWED_BIN_OPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)
_ALLOWED_UNARY_OPS = (ast.UAdd, ast.USub)

# 允许调用的函数白名单（仅一元函数），防止任意函数调用
_ALLOWED_FUNCS = frozenset(
    {
        "sqrt", "sin", "cos", "tan", "asin", "acos", "atan",
        "ln", "log", "exp", "factorial", "abs",
    }
)
# 常量白名单（高精度字面量）
_CONSTANTS = {
    "pi": Decimal("3.1415926535897932384626433832795028841971693993751"),
    "e": Decimal("2.7182818284590452353602874713526624977572470937"),
}


class ExpressionError(ValueError):
    """表达式非法时的异常，message 可直接展示给用户。"""


def evaluate(expression: str) -> Decimal:
    """解析并计算表达式，返回 Decimal 结果；表达式非法时抛出 ExpressionError。"""
    expr = expression.strip()
    if not expr:
        raise ExpressionError("表达式不能为空")
    if len(expr) > MAX_LENGTH:
        raise ExpressionError(f"表达式长度不能超过 {MAX_LENGTH} 个字符")

    _validate_chars(expr)

    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise ExpressionError(f"语法错误：{e.msg}") from e

    _validate_tree(tree, expr)

    try:
        result = _eval_node(tree.body, expr)
    except DivisionByZero:
        raise ExpressionError("除数不能为零") from None
    except InvalidOperation:
        raise ExpressionError("数值运算错误") from None

    return result


def _validate_chars(expr: str) -> None:
    for ch in expr:
        if ch not in _ALLOWED_CHARS:
            raise ExpressionError(f"包含非法字符：{ch!r}")


def _validate_tree(node: ast.AST, source: str, depth: int = 0) -> None:
    """递归校验 AST：只放行白名单内的节点/函数/常量，并限制嵌套深度。"""
    if depth > MAX_DEPTH:
        raise ExpressionError(f"表达式嵌套层级不能超过 {MAX_DEPTH}")

    if isinstance(node, ast.Expression):
        _validate_tree(node.body, source, depth + 1)
    elif isinstance(node, ast.BinOp):
        if type(node.op) not in _ALLOWED_BIN_OPS:
            raise ExpressionError("不支持的二元运算符")
        _validate_tree(node.left, source, depth + 1)
        _validate_tree(node.right, source, depth + 1)
    elif isinstance(node, ast.UnaryOp):
        if type(node.op) not in _ALLOWED_UNARY_OPS:
            raise ExpressionError("不支持的一元运算符")
        _validate_tree(node.operand, source, depth + 1)
    elif isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise ExpressionError("仅支持数字常量")
    elif isinstance(node, ast.Name):
        if node.id not in _CONSTANTS:
            raise ExpressionError(f"未知的标识符：{node.id}")
    elif isinstance(node, ast.Call):
        if (
            isinstance(node.func, ast.Name)
            and node.func.id in _ALLOWED_FUNCS
            and len(node.args) == 1
            and not node.keywords
        ):
            _validate_tree(node.args[0], source, depth + 1)
        else:
            raise ExpressionError("不支持的函数调用")
    else:
        raise ExpressionError(f"不支持的元素：{type(node).__name__}")


def _eval_node(node: ast.AST, source: str) -> Decimal:
    if isinstance(node, ast.Constant):
        # 从原始源码读取数字字面量，避免 Python 先解析成 float 损失精度
        literal = ast.get_source_segment(source, node)
        if literal is None:  # 理论上不会发生，做防御性兜底
            literal = repr(node.value)
        return Decimal(literal)

    if isinstance(node, ast.Name):
        return _CONSTANTS[node.id]

    if isinstance(node, ast.BinOp):
        left = _eval_node(node.left, source)
        right = _eval_node(node.right, source)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        if isinstance(node.op, ast.Pow):
            # 限制底数/指数范围，防止超大幂运算拖垮服务
            if abs(right) > 1000:
                raise ExpressionError("指数过大")
            if abs(left) > 10**9:
                raise ExpressionError("底数过大")
            return left ** right
        raise ExpressionError("不支持的二元运算符")

    if isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand, source)
        if isinstance(node.op, ast.UAdd):
            return +operand
        if isinstance(node.op, ast.USub):
            return -operand
        raise ExpressionError("不支持的一元运算符")

    if isinstance(node, ast.Call):
        name = node.func.id
        arg = _eval_node(node.args[0], source)
        return _eval_func(name, arg)

    raise ExpressionError("不支持的表达式")


def _eval_func(name: str, x: Decimal) -> Decimal:
    if name == "sqrt":
        if x < 0:
            raise ExpressionError("负数不能开平方")
        return x.sqrt()
    if name == "abs":
        return abs(x)
    if name == "factorial":
        if x != x.to_integral_value() or x < 0:
            raise ExpressionError("阶乘仅支持非负整数")
        n = int(x)
        if n > 1000:
            raise ExpressionError("阶乘数值过大")
        return Decimal(math.factorial(n))

    # 超越函数（浮点实现，三角函数按角度制）
    try:
        fx = float(x)
        if name == "sin":
            v = math.sin(math.radians(fx))
        elif name == "cos":
            v = math.cos(math.radians(fx))
        elif name == "tan":
            v = math.tan(math.radians(fx))
        elif name == "asin":
            v = math.degrees(math.asin(fx))
        elif name == "acos":
            v = math.degrees(math.acos(fx))
        elif name == "atan":
            v = math.degrees(math.atan(fx))
        elif name == "ln":
            v = math.log(fx)
        elif name == "log":
            v = math.log10(fx)
        elif name == "exp":
            v = math.exp(fx)
        else:
            raise ExpressionError(f"不支持的函数：{name}")
    except ValueError:
        raise ExpressionError("函数定义域错误") from None
    except OverflowError:
        raise ExpressionError("数值溢出") from None

    if not math.isfinite(v):
        raise ExpressionError("数值溢出")
    # 四舍五入到 12 位小数，消除浮点噪声（如 sin(30) -> 0.5）
    return Decimal(str(round(v, 12)))


def format_result(value: Decimal) -> str:
    """把 Decimal 结果格式化为适合展示的字符串：去掉末尾多余零与负零。"""
    if value.is_zero():
        return "0"
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text

from operator import add, sub, mul, truediv, floordiv, mod, pow, lt, le, eq, ne, ge, gt


OPERATORS = {
    '+': add,
    '-': sub,
    '*': mul,
    '/': truediv,
    '//': floordiv,
    '%': mod,
    '^': pow,
    '<': lt,
    '<=': le,
    '==': eq,
    '!=': ne,
    '>=': ge,
    '>': gt,
    'abs': abs,
    'pow': pow,
    'round': round,
}

# '(sin(213+34.5) - round(32.3))^2'


def validate_brackets(expr, left='(', right=')'):
    count = 0
    for sym in expr:
        if sym == left:
            count += 1
        elif sym == right:
            count -= 1
        if count < 0:
            return False
    if count == 0:
        return True
    return False


def brackets_structure_parser(expr, left='(', right=')'):
    expr = ''.join(expr.split())
    result = []
    content = []
    idx = 0
    expr_len = len(expr)
    while idx < expr_len:
        sym = expr[idx]
        if sym == left:
            if content:
                result.append(''.join(content))
                content = []
            nested_content, jump = brackets_structure_parser(expr[idx + 1:])
            idx += jump
            result.append(nested_content)

        elif sym == right:
            if content:
                result.append(''.join(content))
            return result, idx + 2

        else:
            content.append(sym)
            idx += 1
    if content:
        result.append(''.join(content))
    return result


if __name__ == '__main__':
    print(validate_brackets('()   ()()   ((()))'))
    print(brackets_structure_parser('(sin(213+34.5) - round(32.3))^2'))

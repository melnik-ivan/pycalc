from operator import add, sub, mul, truediv, floordiv, mod, pow, lt, le, eq, ne, ge, gt
from collections import namedtuple
from math import sin


Operator = namedtuple('Operator', 'name function')


OPERATORS = [
    Operator('sin', sin),
    Operator('abs', abs),
    Operator('pow', pow),
    Operator('round', round),
    Operator('^', pow),
    Operator('*', mul),
    Operator('//', floordiv),
    Operator('/', truediv),
    Operator('%', mod),
    Operator('+', add),
    Operator('-', sub),
    Operator('<=', le),
    Operator('<', lt),
    Operator('==', eq),
    Operator('!=', ne),
    Operator('>=', ge),
    Operator('>', gt),
]


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


def cut_operator(expr, operators=OPERATORS):
    for operator in operators:
        if expr.startswith(operator.name):
            return operator.function, expr.lstrip(operator.name)
    return None, expr


def cut_float(expr, numbers='0123456789.'):
    number = ''
    for sym in expr:
        if sym in numbers:
            number += sym
        else:
            break
    if number:
        expr = expr.lstrip(number)
        number = float(number)
        return number, expr
    return None, expr


def type_parser(brackets_structure, operators=OPERATORS):
    result = []
    for x in brackets_structure:
        if type(x) is str:
            while x:
                res, x = cut_float(x)
                if res is not None:
                    result.append(res)
                res, x = cut_operator(x, operators=operators)
                if res is not None:
                    result.append(res)
        if type(x) is list:
            result.append(type_parser(x, operators=operators))
    return result


if __name__ == '__main__':
    print(validate_brackets('()   ()()   ((()))'))
    print(type_parser(brackets_structure_parser('(sin(213+34.5) - round(32.3))^2*0l')))
    print('done')

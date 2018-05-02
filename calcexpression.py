from operator import add, sub, mul, truediv, floordiv, mod, pow, lt, le, eq, ne, ge, gt
from collections import namedtuple
from math import sin, pi

Callable = namedtuple('Callable', 'pattern execute')
Operator = namedtuple('Operator', 'pattern execute weight unary')
Constant = namedtuple('Constant', 'pattern value')
Bracket = namedtuple('Bracket', 'side level')


def comma_operator(left, right):
    if type(left) is tuple and type(right) is tuple:
        return left + right
    elif type(left) is not tuple and type(right) is not tuple:
        return left, right
    elif type(left) is tuple:
        return left + (right,)
    elif type(right) is tuple:
        return (left, ) + right
    else:
        raise TypeError


CONSTANTS = [
    Constant('pi', pi)
]

CALLABLE_OBJECTS = [
    Callable('sin', sin),
    Callable('abs', abs),
    Callable('pow', pow),
    Callable('round', round),
]

OPERATORS = [
    Operator(',', comma_operator, 13, None),
    Operator('^', pow, 12, None),
    Operator('*', mul, 11, None),
    Operator('//', floordiv, 9, None),
    Operator('/', truediv, 10, None),
    Operator('%', mod, 8, None),
    Operator('+', add, 7, lambda x: 0 + x),
    Operator('-', sub, 6, lambda x: 0 - x),
    Operator('<=', le, 4, None),
    Operator('<', lt, 5, None),
    Operator('==', eq, 3, None),
    Operator('!=', ne, 2, None),
    Operator('>=', ge, 0, None),
    Operator('>', gt, 1, None),
]

OPERATORS.sort(key=lambda op: op.weight)

# Todo: brackets validator


def have_external_brackets(expr, bracket_left='(', bracket_right=')'):
    if not (expr.startswith(bracket_left) and expr.endswith(bracket_right)):
        return False
    brackets_level = 0
    for sym in expr[:-1]:
        if sym == bracket_left:
            brackets_level += 1
        elif sym == bracket_right:
            brackets_level -= 1
            if brackets_level == 0:
                return False
    return True


def cut_out_external_brackets(expr, bracket_left='(', bracket_right=')'):
    while have_external_brackets(expr, bracket_left=bracket_left, bracket_right=bracket_right):
        expr = expr[1:-1]
    return expr


def replace_brackets_content(expr, placeholder='@', bracket_left='(', bracket_right=')'):
    result = []
    brackets_level = 0
    for sym in expr:
        if sym == bracket_left:
            brackets_level += 1
            result.append(placeholder)
        elif sym == bracket_right:
            brackets_level -= 1
            result.append(placeholder)
        elif brackets_level > 0:
            result.append(placeholder)
        elif brackets_level == 0:
            result.append(sym)
        else:
            raise SyntaxError('invalid brackets structure')
    return ''.join(result)


def min_weight_slice(expr, subjects, _sorted=True):
    if not _sorted:
        subjects = sorted(subjects, key=lambda x: x.weight)
    for subject in subjects:
        if subject.pattern in expr:
            idx0 = expr.find(subject.pattern)
            idx1 = idx0 + len(subject.pattern)
            return idx0, idx1
    return None


def get_subject(pattern, subjects):
    for subject in subjects:
        if subject.pattern == pattern:
            return subject
    return None


def get_number(pattern):
    try:
        return int(pattern)
    except ValueError:
        pass

    try:
        return float(pattern)
    except ValueError:
        pass
    return None


def execute(expr, bracket_left='(', bracket_right=')', operators=OPERATORS, callable_objects=CALLABLE_OBJECTS, constants=CONSTANTS):
    expr = cut_out_external_brackets(expr)
    expr_replaced = replace_brackets_content(expr)
    result = get_number(expr)
    if result is not None:
        return result
    result = get_subject(expr, constants)
    if result is not None:
        return result.value

    operator_idx = min_weight_slice(expr_replaced, operators)
    if operator_idx:
        left, op, right = expr[:operator_idx[0]], expr[operator_idx[0]: operator_idx[1]], expr[operator_idx[1]:]
        op = get_subject(op, operators)
        if (left != '') and (right != ''):
            return op.execute(execute(left), execute(right))
        elif right and left == '':
            if op.unary:
                return op.unary(execute(right))
            else:
                raise SyntaxError('03')
        else:
            raise SyntaxError('01')

    callable_idx = min_weight_slice(expr_replaced, callable_objects)
    if callable_idx:
        clb, right = expr[callable_idx[0]: callable_idx[1]], expr[callable_idx[1]:]
        clb = get_subject(clb, callable_objects)
        if right != '':
            res = execute(right)
            if type(res) is tuple:
                return clb.execute(*res)
            else:
                return clb.execute(res)
        else:
            return clb.execute()

    raise SyntaxError('02')


if __name__ == '__main__':
    from moduleloader import ModulesScope
    m = ModulesScope(('math', 'builtins'))
    constants = m.get_constants()
    callable_objects = m.get_callable_objects()

    print(execute('(sin(213+34.5)-round(32.3))^2', callable_objects=callable_objects, constants=constants))
    print(execute('25%4', callable_objects=callable_objects, constants=constants))

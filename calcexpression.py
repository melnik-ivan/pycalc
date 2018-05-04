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
    Operator(',', comma_operator, -1, None),
    Operator('^', pow, 12, None),
    Operator('*', mul, 11, None),
    Operator('//', floordiv, 9, None),
    Operator('/', truediv, 10, None),
    Operator('%', mod, 8, None),
    Operator('+', add, 6, lambda x: 0 + x),
    Operator('-', sub, 7, lambda x: 0 - x),
    Operator('<=', le, 4, None),
    Operator('<', lt, 5, None),
    Operator('==', eq, 3, None),
    Operator('!=', ne, 2, None),
    Operator('>=', ge, 0, None),
    Operator('>', gt, 1, None),
]

OPERATORS.sort(key=lambda op: op.weight)


class Expression:
    def __init__(self, expr, bracket_left='(', bracket_right=')', brackets_content_placeholder='#', operators=OPERATORS,
                 callable_objects=CALLABLE_OBJECTS, constants=CONSTANTS):

        self._expr = ''.join(expr.split())
        self.validate()
        self._bracket_left = bracket_left
        self._bracket_right = bracket_right
        self._brackets_content_placeholder = brackets_content_placeholder
        self._operators = sorted(operators, key=lambda x: x.weight)
        self._callable_objects = callable_objects
        self._constants = constants

    def execute(self):
        return self._execute(self._expr)

    def _execute(self, expr):
        expr = self._cut_out_external_brackets(expr)
        expr_replaced = self._replace_brackets_content(expr)
        result = self._get_number(expr)
        if result is not None:
            return result
        result = self._get_constant(expr)
        if result is not None:
            return result.value

        operator_idx = self._get_min_weight_operator_slice(expr_replaced)
        if operator_idx:
            left, op, right = expr[:operator_idx[0]], expr[operator_idx[0]: operator_idx[1]], expr[operator_idx[1]:]
            op = self._get_operator(op)
            if (left != '') and (right != ''):
                return op.execute(self._execute(left), self._execute(right))
            elif right and left == '':
                if op.unary:
                    return op.unary(self._execute(right))
                else:
                    raise SyntaxError('03')
            else:
                raise SyntaxError('01')

        callable_idx = self._get_callable_slice(expr_replaced)
        if callable_idx:
            clb, right = expr[callable_idx[0]: callable_idx[1]], expr[callable_idx[1]:]
            clb = self._get_callable(clb)
            if right != '':
                res = self._execute(right)
                if type(res) is tuple:
                    return clb.execute(*res)
                else:
                    return clb.execute(res)
            else:
                return clb.execute()

        raise SyntaxError('02')

    def validate(self):
        # Todo: validators
        pass

    def _cut_out_external_brackets(self, expr):
        while self._have_external_brackets(expr):
            expr = expr[1:-1]
        return expr

    def _have_external_brackets(self, expr):
        if not (expr.startswith(self._bracket_left) and expr.endswith(self._bracket_right)):
            return False
        brackets_level = 0
        for sym in expr[:-1]:
            if sym == self._bracket_left:
                brackets_level += 1
            elif sym == self._bracket_right:
                brackets_level -= 1
                if brackets_level == 0:
                    return False
        return True

    def _replace_brackets_content(self, expr):
        result = []
        brackets_level = 0
        for sym in expr:
            if sym == self._bracket_left:
                brackets_level += 1
                result.append(self._brackets_content_placeholder)
            elif sym == self._bracket_right:
                brackets_level -= 1
                result.append(self._brackets_content_placeholder)
            elif brackets_level > 0:
                result.append(self._brackets_content_placeholder)
            elif brackets_level == 0:
                result.append(sym)
            else:
                raise SyntaxError('invalid brackets structure')
        return ''.join(result)

    def _get_min_weight_operator_slice(self, expr):
        for op in self._operators:
            if op.pattern in expr:
                idx0 = expr.find(op.pattern)
                idx1 = idx0 + len(op.pattern)
                if not self._endswith_operator(expr[:idx0]):
                    return idx0, idx1
        return None

    def _get_callable_slice(self, expr):
        for clb in self._callable_objects:
            if clb.pattern in expr:
                idx0 = expr.find(clb.pattern)
                idx1 = idx0 + len(clb.pattern)
                return idx0, idx1
        return None

    def _get_object(self, pattern, objects):
        for obj in objects:
            if obj.pattern == pattern:
                return obj
        return None

    def _get_operator(self, pattern):
        return self._get_object(pattern, self._operators)

    def _get_callable(self, pattern):
        return self._get_object(pattern, self._callable_objects)

    def _get_constant(self, pattern):
        return self._get_object(pattern, self._constants)

    def _get_number(self, pattern):
        try:
            return int(pattern)
        except ValueError:
            pass

        try:
            return float(pattern)
        except ValueError:
            pass
        return None

    def _endswith_operator(self, expr):
        for op in self._operators:
            if expr.endswith(op.pattern):
                return True
        return False


if __name__ == '__main__':
    from moduleloader import ModulesScope
    m = ModulesScope(('math', 'builtins'))
    constants = m.get_constants()
    callable_objects = m.get_callable_objects()

    print(Expression('round(pi*2, 3)', callable_objects=callable_objects, constants=constants).execute())

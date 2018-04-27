from operator import add, sub, mul, truediv, floordiv, mod, pow, lt, le, eq, ne, ge, gt
from collections import namedtuple
from math import sin, pi

Func = namedtuple('Func', 'name execute weight')
Operator = namedtuple('Operator', 'name execute weight can_by_unary')
Constant = namedtuple('Constant', 'name value')
Bracket = namedtuple('Bracket', 'side level')

CONSTANTS = [
    Constant('pi', pi)
]

FUNCTIONS = [
    Func('sin', sin, 100),
    Func('abs', abs, 100),
    Func('pow', pow, 100),
    Func('round', round, 100),
]

OPERATORS = [
    Operator('^', pow, 12, False),
    Operator('*', mul, 11, False),
    Operator('//', floordiv, 10, False),
    Operator('/', truediv, 9, False),
    Operator('%', mod, 8, False),
    Operator('+', add, 7, True),
    Operator('-', sub, 6, True),
    Operator('<=', le, 5, False),
    Operator('<', lt, 4, False),
    Operator('==', eq, 3, False),
    Operator('!=', ne, 2, False),
    Operator('>=', ge, 1, False),
    Operator('>', gt, 0, False),
]


class Expression:
    # Todo: Docstring, unittests
    def __init__(
            self,
            expr,
            funcs=None,
            ops=None,
            consts=None,
            bracket_left='(',
            bracket_right=')',
            float_symbols='0123456789.'
    ):
        # Todo: Docstring, unittests
        self._expr = ''.join(expr.split())
        self._rendered_expr = []
        self._funcs = funcs or FUNCTIONS
        self._ops = ops or OPERATORS
        self._consts = consts or CONSTANTS
        self._float_symbols = float_symbols
        self._bracket_left = bracket_left
        self._bracket_right = bracket_right
        self._bracket_level = 0
        self._scissors = []
        self.scissors_registrar()

    def validate_brackets(self):
        # Todo: Docstring, unittests
        count = 0
        for sym in self._expr:
            if sym == self._bracket_left:
                count += 1
            elif sym == self._bracket_right:
                count -= 1
            if count < 0:
                return False
        if count == 0:
            return True
        return False

    def scissors_registrar(self):
        # Todo: Docstring, unittests
        for name, attr in self.__class__.__dict__.items():
            if name.endswith('scissor'):
                if attr not in self._scissors:
                    self._scissors.append(attr)

    def float_scissor(self, shift):
        # Todo: Docstring, unittests
        number = ''
        for sym in self._expr[shift:]:
            if sym in self._float_symbols:
                number += sym
            else:
                break
        if number:
            num_len = len(number)
            number = float(number)
            return number, num_len
        return None, 0

    def const_scissor(self, shift):
        # Todo: Docstring, unittests
        expr = self._expr[shift:]
        for const in self._consts:
            if expr.startswith(const.name):
                return const.value, len(const.name)
        return None, 0

    def bracket_scissor(self, shift):
        # Todo: Docstring, unittests
        expr = self._expr[shift:]
        if expr[0] == self._bracket_left:
            self._bracket_level += 1
            return Bracket('left', self._bracket_level), len(self._bracket_left)
        if expr[0] == self._bracket_right:
            res = Bracket('right', self._bracket_level), len(self._bracket_left)
            self._bracket_level -= 1
            return res
        return None, 0

    def func_scissor(self, shift):
        # Todo: Docstring, unittests
        expr = self._expr[shift:]
        for func in self._funcs:
            if expr.startswith(func.name):
                return func, len(func.name)
        return None, 0

    def operator_scissor(self, shift):
        # Todo: Docstring, unittests
        expr = self._expr[shift:]
        for operator in self._ops:
            if expr.startswith(operator.name):
                return operator, len(operator.name)
        return None, 0

    def render_expr(self):
        # Todo: Docstring, unittests
        result = []
        expr_len = len(self._expr)
        shift_count = 0
        prev_shift_count = 0
        while shift_count < expr_len:
            for scissor in self._scissors:
                if shift_count == expr_len:
                    break
                res, shift = scissor(self, shift_count)
                if shift > 0:
                    shift_count += shift
                    result.append(res)
            if shift_count == prev_shift_count:
                print('error')  # Todo: Exception
                return
            prev_shift_count = shift_count
        self._rendered_expr = result


if __name__ == '__main__':
    from pprint import pprint
    e = Expression('(sin(213+34.5) - round(32.3))^2*0')
    e.render_expr()
    pprint(e._rendered_expr)

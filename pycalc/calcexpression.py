from operator import add, sub, mul, truediv, floordiv, mod, pow, lt, le, eq, ne, ge, gt
from collections import namedtuple
from pycalc.moduleloader import built_ins
import re

Operator = namedtuple('Operator', 'pattern execute weight unary')
Bracket = namedtuple('Bracket', 'side level')


def comma_operator(left, right):
    if type(left) is tuple and type(right) is tuple:
        return left + right
    elif type(left) is not tuple and type(right) is not tuple:
        return left, right
    elif type(left) is tuple:
        return left + (right,)
    elif type(right) is tuple:
        return (left,) + right
    else:
        raise TypeError


CONSTANTS = built_ins.get_constants()

CALLABLE_OBJECTS = built_ins.get_callable_objects()

OPERATORS = [
    Operator(',', comma_operator, -1, None),
    Operator('^', pow, 12, None),
    Operator('*', mul, 11, None),
    Operator('//', floordiv, 9, None),
    Operator('/', truediv, 10, None),
    Operator('%', mod, 8, None),
    Operator('+', add, 6, lambda x: x),
    Operator('-', sub, 7, lambda x: -x),
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
        self._bracket_left = bracket_left
        self._bracket_right = bracket_right
        self._expr = expr
        self._preprocessing()
        self.validate()
        self._brackets_content_placeholder = brackets_content_placeholder
        self._operators = sorted(operators, key=lambda x: x.weight)
        self._callable_objects = callable_objects
        self._constants = constants

    def _preprocessing(self):
        self._expr = ''.join(self._expr.split())
        self._uncover_multiplication()

    def execute(self):
        return self._execute(self._expr)

    def _execute(self, expr):
        expr = self._cut_out_external_brackets(expr)
        expr_replaced = self._replace_brackets_content(expr)

        result = self._get_number(expr)
        if result is not None:
            return result

        result = self._get_object(expr, self._constants)
        if result is not None:
            return result.value

        execute_list = [
            (self._execute_binary_operator, (expr, expr_replaced), {'filter_': lambda x: x.pattern != '^'}),
            (self._execute_unary_operator, (expr, expr_replaced),
             {'filter_': lambda x: x.pattern == '-' or x.pattern == '+'}),
            (self._execute_binary_operator, (expr, expr_replaced),
             {'filter_': lambda x: x.pattern == '^', 'revert': False}),
            (self._execute_callable_object, (expr, expr_replaced), {}),
        ]

        for func, args, kwargs in execute_list:
            result = func(*args, **kwargs)
            if result[0]:
                return result[1]

        raise SyntaxError('01')

    def _execute_binary_operator(self, expr, expr_replaced, filter_=None, revert=True):
        operator_idx = self._get_min_weight_binary_operator(expr_replaced, filter_, revert)
        if operator_idx:
            left, op, right = expr[:operator_idx[0]], expr[operator_idx[0]: operator_idx[1]], expr[operator_idx[1]:]
            op = self._get_object(op, self._operators, filter_)
            if (left != '') and (right != ''):
                return True, op.execute(self._execute(left), self._execute(right))
            elif left != '' and right == '':
                return True, op.execute(self._execute(left))
            else:
                raise SyntaxError('02')
        return False, None

    def _execute_unary_operator(self, expr, expr_replaced, filter_=None):
        unary_idx = self._get_min_weight_unary_operator(expr_replaced, filter_)
        if unary_idx:
            left, op, right = expr[:unary_idx[0]], expr[unary_idx[0]: unary_idx[1]], expr[unary_idx[1]:]
            op = self._get_object(op, self._operators, filter_)
            if right and left == '':
                if op.unary:
                    return True, op.unary(self._execute(right))
                else:
                    raise SyntaxError('03')
        return False, None

    def _execute_callable_object(self, expr, expr_replaced, filter_=None):
        callable_idx = self._get_callable_slice(expr_replaced, filter_)
        if callable_idx:
            left, clb, right = expr[:callable_idx[0]], expr[callable_idx[0]: callable_idx[1]], expr[callable_idx[1]:]
            if left and not self._get_min_weight_unary_operator(left):
                raise SyntaxError('04')
            clb = self._get_object(clb, self._callable_objects, filter_)
            if right != '':
                res = self._execute(right)
                if type(res) is tuple:
                    return True, clb.execute(*res)
                else:
                    return True, clb.execute(res)
            else:
                return True, clb.execute()
        return False, None

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

    def _operator_is_unary(self, expr, idx0):
        return bool(not expr[:idx0] or expr[:idx0].endswith(self._bracket_left) or self._endswith_operator(expr[:idx0]))

    def _get_min_weight_binary_operator(self, expr, filter_=None, revert=True):
        operators = self._operators
        if filter_:
            operators = filter(filter_, operators)
        for op in operators:
            if op.pattern in expr:
                idx0 = -1
                idx1 = 0
                while True:
                    if not revert:
                        idx0 = expr[idx1:].find(op.pattern)
                        if idx0 < 0:
                            break
                        idx1 = idx0 + len(op.pattern)
                        if not self._operator_is_unary(expr, idx0):
                            return idx0, idx1
                    else:
                        idx0 = expr[:idx0].rfind(op.pattern)
                        if idx0 < 0:
                            break
                        idx1 = idx0 + len(op.pattern)
                        if not self._operator_is_unary(expr, idx0):
                            return idx0, idx1
        return None

    def _get_min_weight_unary_operator(self, expr, filter_=None):
        operators = self._operators
        if filter_:
            operators = filter(filter_, operators)
        min_idxs = None
        for op in operators:
            if op.pattern in expr:
                idx0 = expr.find(op.pattern)
                idx1 = idx0 + len(op.pattern)
                if self._operator_is_unary(expr, idx0):
                    if min_idxs and min_idxs[0] > idx0:
                        min_idxs = idx0, idx1
                    if not min_idxs:
                        min_idxs = idx0, idx1
        return min_idxs

    def _get_callable_slice(self, expr, filter_=None):
        callable_objects = self._callable_objects
        if filter_:
            callable_objects = filter(filter_, callable_objects)
        for clb in callable_objects:
            if clb.pattern in expr:
                idx0 = expr.find(clb.pattern)
                idx1 = idx0 + len(clb.pattern)
                return idx0, idx1
        return None

    @staticmethod
    def _get_object(pattern, objects, filter_=None):
        if filter_:
            objects = filter(filter_, objects)
        for obj in objects:
            if obj.pattern == pattern:
                return obj
        return None

    @staticmethod
    def _get_number(pattern):
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
                return op.pattern
        return None

    def _startswith_operator(self, expr):
        for op in self._operators:
            if expr.startswith(op.pattern):
                return op.pattern
        return None

    def _uncover_multiplication(self):
        rx1 = r'[\W](\d*\.?\d+?\{})'
        rx2 = r'^(\d*\.?\d+?\{})'

        for rx in rx1, rx2:
            bracket = self._bracket_left
            match_list = re.findall(rx.format(bracket), self._expr)
            for match in match_list:
                replacer = ''.join((match[:-1], '*', match[-1]))
                self._expr = self._expr.replace(match, replacer)

            reversed_expr = self._expr[::-1]

            bracket = self._bracket_right
            match_list = re.findall(rx.format(bracket), reversed_expr)
            for match in match_list:
                replacer = ''.join((match[:-1], '*', match[-1]))
                reversed_expr = reversed_expr.replace(match, replacer)

            self._expr = reversed_expr[::-1]

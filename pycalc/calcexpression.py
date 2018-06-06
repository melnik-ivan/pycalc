"""
This module provides expression parsing tools.
"""

from operator import add, sub, mul, truediv, floordiv, mod, lt, le, eq, ne, ge, gt
from collections import namedtuple
import re

from pycalc.moduleloader import BUILT_INS
from pycalc.exceptions import PyCalcSyntaxError

Operator = namedtuple('Operator', 'pattern execute weight unary')


def comma_operator(left, right):
    """
    Imitates python comma operator. If one of operands is tuple,
    unpacks this operand. Returns tuple of operands.

    Positional arguments:
        left: left operand
        right: right operand

    return: tuple(*operands)
    """
    if isinstance(left, tuple) and isinstance(right, tuple):
        return left + right
    elif not isinstance(left, tuple) and not isinstance(right, tuple):
        return left, right
    elif isinstance(left, tuple):
        return left + (right,)
    elif isinstance(right, tuple):
        return (left,) + right
    else:
        raise PyCalcSyntaxError('invalid syntax near ","')


CONSTANTS = BUILT_INS.get_constants()

CALLABLE_OBJECTS = BUILT_INS.get_callable_objects()

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
    """
    Generates expression model from string.
    """

    def __init__(self, expr, operators=None, callable_objects=None, constants=None):
        """
        Positional arguments:
            expr: string with python-like (except power operator '^'
                and syntax of abridged multiplication: '2(3+4)') expression.

        Optional keyword arguments:
            bracket_left: character of left bracket.
            bracket_right: character of right bracket.
            brackets_content_placeholder: character to be used as a stub
                instead brackets content for temporary expressions.
            operators: list of operators where operator is object with
                attributes: pattern, execute, weight and unary
            callable_objects: list of callable objects where callable object
                is object with attributes: pattern and execute
            constants: list of constants objects where constant is object
                with attributes: pattern and execute
        """
        self._bracket_left = '('
        self._bracket_right = ')'
        self._expr = expr
        self._brackets_content_placeholder = '#'
        operators = operators or OPERATORS
        callable_objects = callable_objects or CALLABLE_OBJECTS
        constants = constants or CONSTANTS
        self._operators = sorted(operators, key=lambda x: x.weight)
        self._callable_objects = list(callable_objects)
        self._constants = list(constants)
        self.validate()
        self._preprocessing()

    def _preprocessing(self):
        """
        Prepares input string for parsing
        """
        self._expr = ''.join(self._expr.split())
        self._uncover_multiplication()

    def execute(self):
        """
        Launches parsing and execution process.
        Returns result of execution.
        """
        return self._execute(self._expr)

    def _execute(self, expr):
        """
        Implements execution logic and parsing order.
        """
        expr = self._cut_out_external_brackets(expr)
        expr_replaced = self._replace_brackets_content(expr)

        result = self._get_number(expr)
        if result is not None:
            return result

        result = self._get_object(expr, self._constants)
        if result is not None:
            return result.value

        execute_list = [
            (self._execute_binary_operator, (expr, expr_replaced),
             {'filter_': lambda x: x.pattern != '^'}),
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

        raise PyCalcSyntaxError('invalid syntax near "{}"'.format(expr))

    def _execute_binary_operator(self, expr, expr_replaced, filter_=None, revert=True):
        """
        Implements execution logic for binary operators only.
        """
        operator_idx = self._get_min_weight_binary_operator(expr_replaced, filter_, revert)
        if operator_idx:
            left = expr[:operator_idx[0]]
            operator = expr[operator_idx[0]: operator_idx[1]]
            right = expr[operator_idx[1]:]
            operator = self._get_object(operator, self._operators, filter_)
            if (left != '') and (right != ''):
                return True, operator.execute(self._execute(left), self._execute(right))
            elif left != '' and right == '':
                return True, operator.execute(self._execute(left))
            else:
                PyCalcSyntaxError('invalid syntax near operator "{}"'.format(operator.pattern))
        return False, None

    def _execute_unary_operator(self, expr, expr_replaced, filter_=None):
        """
        Implements execution logic for unary operators only.
        """
        unary_idx = self._get_min_weight_unary_operator(expr_replaced, filter_)
        if unary_idx:
            left = expr[:unary_idx[0]]
            operator = expr[unary_idx[0]: unary_idx[1]]
            right = expr[unary_idx[1]:]
            operator = self._get_object(operator, self._operators, filter_)
            if right and left == '':
                if operator.unary:
                    return True, operator.unary(self._execute(right))
                else:
                    raise PyCalcSyntaxError(
                        'invalid syntax near operator "{}"'.format(operator.pattern)
                    )
        return False, None

    def _execute_callable_object(self, expr, expr_replaced, filter_=None):
        """
        Implements execution logic for callable objects only.
        """
        callable_idx = self._get_callable_slice(expr_replaced, filter_)
        if callable_idx:
            left = expr[:callable_idx[0]]
            clb = expr[callable_idx[0]: callable_idx[1]]
            right = expr[callable_idx[1]:]
            if left and not self._get_min_weight_unary_operator(left):
                PyCalcSyntaxError('invalid syntax near callable object "{}"'.format(clb.pattern))
            clb = self._get_object(clb, self._callable_objects, filter_)
            if right != '':
                res = self._execute(right)
                if isinstance(res, tuple):
                    return True, clb.execute(*res)
                return True, clb.execute(res)
            return True, clb.execute()
        return False, None

    def validate(self):
        """
        Runs validators. If any of them is failed raise corresponding exception.
        """
        self.empty_expression_validator()
        self.spaces_validator()

    def empty_expression_validator(self):
        """
        Verifies that the expression is not empty.
        """
        if not self._expr:
            raise PyCalcSyntaxError('empty expression')

    def spaces_validator(self):
        """
        Verifies that the expression is not contains unexpected spaces.
        """
        operator_patterns = [operator.pattern for operator in self._operators]
        operator_patterns += ['!', '=']
        nun_patterns = [str(integer) for integer in range(10)]
        nun_patterns.append('.')
        unexpected_patterns = ['{} {}'.format(pattern1, pattern2)
                               for pattern1 in operator_patterns
                               for pattern2 in operator_patterns]
        unexpected_patterns += ['{} {}'.format(pattern1, pattern2)
                                for pattern1 in nun_patterns
                                for pattern2 in nun_patterns]
        expected_patterns = ['{} {}'.format(pattern1, pattern2)
                             for pattern1 in ('^', '*', '=', '<', '>', '/')
                             for pattern2 in ('-', '+')]
        for pattern in expected_patterns:
            unexpected_patterns.remove(pattern)
        for unexpected_pattern in unexpected_patterns:
            if unexpected_pattern in self._expr:
                raise PyCalcSyntaxError('unexpected space: "{}"'.format(unexpected_pattern))

    def _cut_out_external_brackets(self, expr):
        """
        Cuts out external brackets from expr.
        """
        while self._have_external_brackets(expr):
            expr = expr[1:-1]
        return expr

    def _have_external_brackets(self, expr):
        """
        Returns True if expr have external brackets else False.
        """
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
        """
        Returns expr with replaced brackets content with self._brackets_content_placeholder.
        """
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
                raise PyCalcSyntaxError('invalid brackets are not balanced')
        return ''.join(result)

    def _operator_is_unary(self, expr, idx0):
        """
        Looks at expr and returns True if operator at idx0 is unary else returns False.
        """
        return bool(not expr[:idx0] or
                    expr[:idx0].endswith(self._bracket_left) or
                    self._endswith_operator(expr[:idx0]))

    def _get_min_weight_binary_operator(self, expr, filter_=None, revert=True):
        """
        Returns binary operator with minimal value of weight from sorted by weight
        self._operators.

        Optional keyword arguments:
            filter_: filter function what be applied to the operators list
            revert: change direction of searching operators True (Default) <-
        """
        operators = self._operators
        if filter_:
            operators = filter(filter_, operators)
        for operator in operators:
            if operator.pattern in expr:
                idx0 = -1
                idx1 = 0
                while True:
                    if not revert:
                        idx0 = expr[idx1:].find(operator.pattern)
                        if idx0 < 0:
                            break
                        idx1 = idx0 + len(operator.pattern)
                        if not self._operator_is_unary(expr, idx0):
                            return idx0, idx1
                    else:
                        idx0 = expr[:idx0].rfind(operator.pattern)
                        if idx0 < 0:
                            break
                        idx1 = idx0 + len(operator.pattern)
                        if not self._operator_is_unary(expr, idx0):
                            return idx0, idx1
        return None

    def _get_min_weight_unary_operator(self, expr, filter_=None):
        """
        Returns unary operator with minimal value of weight from sorted by weight
        self._operators.

        Optional keyword arguments:
            filter_: filter function what be applied to the operators list
        """
        operators = self._operators
        if filter_:
            operators = filter(filter_, operators)
        min_indexes = ()
        for operator in operators:
            if operator.pattern in expr:
                idx0 = expr.find(operator.pattern)
                idx1 = idx0 + len(operator.pattern)
                if self._operator_is_unary(expr, idx0):
                    if min_indexes and min_indexes[0] > idx0:
                        min_indexes = idx0, idx1
                    if not min_indexes:
                        min_indexes = idx0, idx1
        return min_indexes or None

    def _get_callable_slice(self, expr, filter_=None):
        """
        Returns expr slice of callable object from self._callable_objects.

        Optional keyword arguments:
            filter_: filter function what be applied to the callable objects list
        """
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
        """
        Returns object from objects where object.pattern equal to pattern argument.

        Optional keyword arguments:
            filter_: filter function what be applied to the objects list
        """
        if filter_:
            objects = filter(filter_, objects)
        for obj in objects:
            if obj.pattern == pattern:
                return obj
        return None

    @staticmethod
    def _get_number(pattern):
        """
        Returns float or int if pattern match for the corresponding constructor, else
        returns None.
        """
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
        """
        Returns pattern of operator if expr endswith on it, else returns None.
        """
        for operator in self._operators:
            if expr.endswith(operator.pattern):
                return operator.pattern
        return None

    def _startswith_operator(self, expr):
        """
        Returns pattern of operator if expr startswith on it, else returns None.
        """
        for operator in self._operators:
            if expr.startswith(operator.pattern):
                return operator.pattern
        return None

    def _uncover_multiplication(self):
        """
        Uncovers shortened multiplication in self._expr.

        Example: '2(2+2)' -> '2*(2+2)'
        """
        regular_expression_1 = r'[\W](\d*\.?\d+?\{})'
        regular_expression_2 = r'^(\d*\.?\d+?\{})'

        for regular_expression in regular_expression_1, regular_expression_2:
            bracket = self._bracket_left
            match_list = re.findall(regular_expression.format(bracket), self._expr)
            for match in match_list:
                replacer = ''.join((match[:-1], '*', match[-1]))
                self._expr = self._expr.replace(match, replacer)

            reversed_expr = self._expr[::-1]

            bracket = self._bracket_right
            match_list = re.findall(regular_expression.format(bracket), reversed_expr)
            for match in match_list:
                replacer = ''.join((match[:-1], '*', match[-1]))
                reversed_expr = reversed_expr.replace(match, replacer)

            self._expr = reversed_expr[::-1]

import os
import unittest
from collections import namedtuple
from math import pi, e, log, sin, log10, cos

from pycalc.calcexpression import Expression, OPERATORS, CALLABLE_OBJECTS, CONSTANTS
from pycalc.exceptions import PyCalcSyntaxError
from pycalc.moduleloader import ModulesScope
from pycalc.__main__ import main as pycalc_main


class TestExpressionMethods(unittest.TestCase):

    def setUp(self):
        self.scope = ModulesScope('builtins', 'math')
        self.expr = Expression('2+2', callable_objects=self.scope.get_callable_objects(),
                               constants=self.scope.get_constants())

    def tearDown(self):
        del self.expr
        del self.scope

    def test_init(self):
        arg = 'round(2*(- 5 +9^3), 2)'
        operators = OPERATORS
        callable_objects = CALLABLE_OBJECTS
        constants = CONSTANTS
        self.assertEqual(sorted(operators, key=lambda x: x.weight), Expression(arg, operators=operators)._operators)
        self.assertEqual(callable_objects, Expression(arg, callable_objects=callable_objects)._callable_objects)
        self.assertEqual(constants, Expression(arg, constants=constants)._constants)

    def test_preprocessing(self):
        arg = 'round(2*(- 5 +9^3), 2)'
        self.assertEqual('round(2*(-5+9^3),2)', Expression(arg)._expr)

    def test__execute(self):
        test_list = [
            ('1', 1),
            ('min(range(10))', 0),
            ('-1', -1),
            ('--1', 1),
            ('-1^2', -1 ** 2),
            ('-1^3', -1 ** 3),
            ('2+2*2', 6),
            ('(2+2)*2', 8),
            ('10==10.0', True),
            ('10!=10.0', False),
            ('10^10==10^10', True),
            ('5>4', True),
            ('5<4', False),
            ('5<=4', False),
            ('5>=4', True),
            ('-int(4.0)^2', -int(4.0) ** 2),
            ('-sin(2)^2', -0.826821810431806),
            ('2^2^3', 2 ** 2 ** 3),
            ('2^-3', 2 ** -3),
            ('-2^-3', -2 ** -3),
        ]
        for arg, result in test_list:
            self.assertEqual(result, Expression('2+2', constants=self.scope.get_constants(),
                                                callable_objects=self.scope.get_callable_objects())._execute(arg))

    def test_execute(self):
        test_list = [
            ('1', 1),
            ('min(range(10))', 0),
            ('-1', -1),
            ('--1', 1),
            ('-1^2', -1 ** 2),
            ('-1^3', -1 ** 3),
            ('2+2  *2', 6),
            ('(  2+2)  *2', 8),
            ('10 ==10.0', True),
            ('10 != 10.0', False),
            ('10^10==10^10', True),
            ('5>4', True),
            ('5<4', False),
            ('5<=4', False),
            ('5>=4', True),
        ]
        for arg, result in test_list:
            self.assertEqual(result, Expression(arg).execute())

    def test_execute_binary_operator(self):
        test_list = [
            (('2+2', '2+2', None), (True, 4)),
            (('2+sin(4)', '2+sin' + self.expr._brackets_content_placeholder * 3, None), (True, 1.2431975046920718)),
            (('2+2', '2+2', lambda x: x.pattern != '+'), (False, None)),
        ]
        for args, result in test_list:
            self.assertEqual(result, self.expr._execute_binary_operator(*args))

    def test_execute_unary_operator(self):
        test_list = [
            (('-2', '-2', None), (True, -2)),
            (('+sin(4)', '+sin' + self.expr._brackets_content_placeholder * 3, None), (True, -0.7568024953079282)),
            (('+2', '+2', lambda x: x.pattern != '+'), (False, None)),
        ]
        for args, result in test_list:
            self.assertEqual(result, self.expr._execute_unary_operator(*args))

    def test_execute_callable_object(self):
        test_list = [
            (('-2', '-2', None), (False, None)),
            (('-sin(4)', '-sin' + self.expr._brackets_content_placeholder * 3, None), (True, -0.7568024953079282)),
            (('sin(2)', 'sin' + self.expr._brackets_content_placeholder * 3, lambda x: x.pattern != 'sin'),
             (False, None)),
        ]
        for args, result in test_list:
            self.assertEqual(result, self.expr._execute_callable_object(*args))

    def test_cut_out_external_brackets(self):
        test_list = [
            ('()', ''),
            ('(-4)', '-4'),
            ('()+()', '()+()'),
            ('(adsaf fdsa3248)(()())', '(adsaf fdsa3248)(()())'),
        ]
        for arg, result in test_list:
            self.assertEqual(result, self.expr._cut_out_external_brackets(arg))

    def test_have_external_brackets(self):
        test_list = [
            ('()', True),
            ('(-4)', True),
            ('()+()', False),
            ('(adsaf fdsa3248)(()())', False),
        ]
        for arg, result in test_list:
            self.assertEqual(result, self.expr._have_external_brackets(arg))

    def test_replace_brackets_content(self):
        test_list = [
            ('321(42343)534', '321#######534'),
            ('abs(sin(2))', 'abs########'),
            ('func1(arg) + func2(arg)', 'func1##### + func2#####'),
        ]
        expression = Expression('2+2')
        for arg, result in test_list:
            self.assertEqual(result, expression._replace_brackets_content(arg))

    def test_operator_is_unary(self):
        test_list = [
            (('-2', 0), True),
            (('2--2', 2), True),
            (('2-+2', 1), False),
            (('(+(2))', 1), True),
            (('2+2', 1), False),
        ]
        for args, result in test_list:
            if result:
                self.assertTrue(self.expr._operator_is_unary(*args))
            else:
                self.assertFalse(self.expr._operator_is_unary(*args))

    def test_get_min_weight_binary_operator(self):
        test_list = [
            ('2+-2', {}, (1, 2)),
            ('2-2-2', {}, (3, 4)),
            ('2==2-2', {}, (1, 3)),
            ('2==2', {}, (1, 3)),
            ('2*2+2^2', {}, (3, 4)),
            ('abracadabra', {}, None),
            ('2-3-2', {'revert': False}, (1, 2)),
        ]
        for arg, kwargs, result in test_list:
            self.assertEqual(result, self.expr._get_min_weight_binary_operator(arg, **kwargs))

    def test_get_min_weight_unary_operator(self):
        test_list = [
            ('2+-2', (2, 3)),
            ('2-2-2', None),
            ('2==2-2', None),
            ('2==-2', (3, 4)),
            ('2*2+2^-2', (6, 7)),
        ]
        for arg, result in test_list:
            self.assertEqual(result, self.expr._get_min_weight_unary_operator(arg))

    def test_get_callable_slice(self):
        test_list = [
            ('abracadabra', None),
            ('2-2-2', None),
            ('2==2-2', None),
            ('2+2+(max([12,2,3]))', (5, 8)),
            ('round(3, 6)', (0, 5)),
        ]
        for arg, result in test_list:
            self.assertEqual(result, self.expr._get_callable_slice(arg), 'args: {}'.format(arg))

    def test_get_object(self):
        TestObject = namedtuple('TestObject', 'pattern')
        o1 = TestObject('o1')
        o2 = TestObject('o2')
        objects = (o1, o2)
        test_list = [
            (('o1', objects), o1),
            (('o2', objects), o2),
            (('o3', objects), None),
            (('1', objects), None)
        ]
        for args, result in test_list:
            self.assertIs(result, self.expr._get_object(*args), 'args: {}'.format(args))

    def test_get_number(self):
        test_list = [
            ('1.4', 1.4),
            ('1', 1),
            ('-3', -3),
            ('a2', None),
            ('0x10', None)
        ]
        for arg, result in test_list:
            self.assertEqual(result, self.expr._get_number(arg))

    def test_endswith_operator(self):
        test_list = [
            ('5==', '=='),
            (')+-', '-'),
            ('+sin(4)', None),
            ('sin(4)-3', None),
        ]
        for arg, result in test_list:
            self.assertEqual(result, self.expr._endswith_operator(arg))

    def test_startswith_operator(self):
        test_list = [
            ('5-', None),
            (')+-', None),
            ('>=sin(4)', '>='),
            ('//sin(4)-3', '//'),
        ]
        for arg, result in test_list:
            self.assertEqual(result, self.expr._startswith_operator(arg))

    def test_error_cases(self):
        test_list = [
            "",
            "+",
            "1-",
            "1 2",
            "ee",
            "123e",
            "==7",
            "1 * * 2",
            "1 + 2(3 * 4))",
            "((1+2)",
            "1 + 1 2 3 4 5 6 ",
            "log100(100)",
            "------",
            "5 > = 6",
            "5 / / 6",
            "6 < = 6",
            "6 * * 6",
            "(((((",
        ]
        for arg in test_list:
            with self.assertRaises(PyCalcSyntaxError, msg=arg):
                Expression(arg, callable_objects=CALLABLE_OBJECTS, constants=CONSTANTS, operators=OPERATORS).execute()


class TestE2E(unittest.TestCase):

    def main_assert_equal(self, test_list):
        for arg, result in test_list:
            self.assertEqual(pycalc_main(expr=arg, silent=True), result, msg=arg)

    def test_unary_operators(self):
        test_list = [
            ('-13', -13),
            ('6 - (-13)', (6 - (-13))),
            ('1 ---1', (1 - --1)),
            ('-+---+-1', (- +---+-1)),
        ]
        self.main_assert_equal(test_list)

    def test_operator_priority(self):
        test_list = [
            ('1+2*2', 1 + 2 * 2),
            ('1+(2+32)3', 1 + (2 + 32) * 3),
            ('10*(2+1)', 10 * (2 + 1)),
            ('10^(2+1)', 10 ** (2 + 1)),
            ('100/3^2', 100 / 3 ** 2),
            ('100/3%2^2', 100 / 3 % 2 ** 2),
        ]
        self.main_assert_equal(test_list)

    def test_function_and_constants(self):
        test_list = [
            ('pi+e', pi + e),
            ('log(e)', log(e)),
            ('sin(pi/2)', sin(pi / 2)),
            ('log10(100)', log10(100)),
            ('sin(pi/2)1116', sin(pi / 2) * 1116),
            ('2*sin(pi/2)', 2 * sin(pi / 2)),
        ]
        self.main_assert_equal(test_list)

    def test_associative(self):
        test_list = [
            ("102%12%7", 102 % 12 % 7),
            ("100/4/3", 100 / 4 / 3),
            ("2^3^4", 2 ** 3 ** 4),
        ]
        self.main_assert_equal(test_list)

    def test_comparison_operators(self):
        test_list = [
            ("1+23==1+23", 1 + 23 == 1 + 23),
            ("e^5>=e^5+1", e ** 5 >= e ** 5 + 1),
            ("1+24/3+1!=1+24/3+2", 1 + 24 / 3 + 1 != 1 + 24 / 3 + 2),
        ]
        self.main_assert_equal(test_list)

    def test_common(self):
        test_list = [
            ("(100)", 100),
            ("666", 666),
            ("10(2+1)", 10 * (2 + 1)),
            ("-.1", -.1),
            ("1/3", 1 / 3),
            ("1.0/3.0", 1.0 / 3.0),
            (".1 * 2.0^56.0", .1 * 2.0 ** 56.0),
            ("e^34", e ** 34),
            ("(2.0^(pi/pi+e/e+2.0^0.0))", (2.0 ** (pi / pi + e / e + 2.0 ** 0.0))),
            ("(2.0^(pi/pi+e/e+2.0^0.0))^(1.0/3.0)", (2.0 ** (pi / pi + e / e + 2.0 ** 0.0)) ** (1.0 / 3.0)),
            ("sin(pi/2^1) + log(1*4+2^2+1, 3^2)", sin(pi / 2 ** 1) + log(1 * 4 + 2 ** 2 + 1, 3 ** 2)),
            ("10*e^0*log10(.4* -5/ -0.1-10) --abs(-53/10) +-5",
             10 * e ** 0 * log10(.4 * -5 / -0.1 - 10) - -abs(-53 / 10) + -5),

            (
                "sin(-cos(-sin(3.0)-cos(-sin(-3.0*5.0)-sin(cos(log10(43.0))))+" + \
                "cos(sin(sin(34.0-2.0^2.0))))--cos(1.0)--cos(0.0)^3.0)",
                sin(-cos(
                    -sin(3.0) - cos(-sin(-3.0 * 5.0) - sin(cos(log10(43.0)))) + cos(
                        sin(sin(34.0 - 2.0 ** 2.0)))) - -cos(
                    1.0) - -cos(0.0) ** 3.0)),
            ("2.0^(2.0^2.0*2.0^2.0)",
             2.0 ** (2.0 ** 2.0 * 2.0 ** 2.0)),
            ("sin(e^log(e^e^sin(23.0),45.0) + cos(3.0+log10(e^-e)))",
             sin(e ** log(e ** e ** sin(23.0), 45.0) + cos(3.0 + log10(e ** -e)))),
        ]
        self.main_assert_equal(test_list)


if __name__ == '__main__':
    unittest.main()

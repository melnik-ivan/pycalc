import unittest
from collections import namedtuple
from math import sin

from calcexpression import Expression, OPERATORS, CALLABLE_OBJECTS, CONSTANTS
from moduleloader import ModulesScope


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
        bracket_left = '('
        bracket_right = ')'
        brackets_content_placeholder = '#'
        operators = OPERATORS
        callable_objects = CALLABLE_OBJECTS
        constants = CONSTANTS
        self.assertEqual(bracket_left, Expression(arg, bracket_left=bracket_left)._bracket_left)
        self.assertEqual(bracket_right, Expression(arg, bracket_right=bracket_right)._bracket_right)
        self.assertEqual(
            brackets_content_placeholder,
            Expression(
                arg,
                brackets_content_placeholder=brackets_content_placeholder

            )._brackets_content_placeholder
        )
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
            ('-1^2', eval('-1**2')),
            ('-1^3', eval('-1**3')),
            ('2+2*2', 6),
            ('(2+2)*2', 8),
            ('10==10.0', True),
            ('10!=10.0', False),
            ('10^10==10^10', True),
            ('5>4', True),
            ('5<4', False),
            ('5<=4', False),
            ('5>=4', True),
            ('-int(4.0)^2', eval('-int(4.0)**2')),
            ('-sin(2)^2', -0.826821810431806),
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
            ('-1^2', eval('-1**2')),
            ('-1^3', eval('-1**3')),
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
        placeholder = '#'
        expression = Expression('2+2', brackets_content_placeholder=placeholder)
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
            ('2+-2', (1, 2)),
            ('2-2-2', (3, 4)),
            ('2==2-2', (1, 3)),
            ('2==2', (1, 3)),
            ('2*2+2^2', (3, 4)),
            ('abracadabra', None),
        ]
        for arg, result in test_list:
            self.assertEqual(result, self.expr._get_min_weight_binary_operator(arg))

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


if __name__ == '__main__':
    unittest.main()

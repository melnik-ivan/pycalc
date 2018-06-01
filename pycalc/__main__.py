#!/usr/bin/env python3
"""
Provides console user interface for pycalc.
"""
import argparse
from collections import namedtuple

from pycalc.moduleloader import ModulesScope
from pycalc.calcexpression import Expression
from pycalc.exceptions import exceptions_handler


Arguments = namedtuple("Arguments", "EXPRESSION use_modules")


@exceptions_handler
def main(expr=None, use_modules=None, silent=False):
    """
    Handled arguments of command line, executed expression.
    """
    args = None
    modules = ['builtins', 'math']
    if expr:
        args = Arguments(expr, use_modules)
    if not args:
        parser = argparse.ArgumentParser()
        parser.add_argument('EXPRESSION', help='expression string to evaluate')
        parser.add_argument('-m', '--use-modules', nargs='+', help='additional modules to use')
        args = parser.parse_args()
    if args.use_modules:
        for module in args.use_modules:
            if module not in modules:
                modules.append(module)
    modules_scope = ModulesScope(*modules)
    result = Expression(
        args.EXPRESSION,
        callable_objects=modules_scope.get_callable_objects(),
        constants=modules_scope.get_constants()
    ).execute()
    if not silent:
        print(result)
    return result


if __name__ == '__main__':
    main()

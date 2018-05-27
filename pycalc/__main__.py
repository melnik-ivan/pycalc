#!/usr/bin/env python3
from collections import namedtuple

from pycalc.moduleloader import ModulesScope
from pycalc.calcexpression import Expression
import argparse


Arguments = namedtuple("Arguments", "EXPRESSION use_modules")


def main(console_mod=True, expr=None, use_modules=None):
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
        for m in args.use_modules:
            if m not in modules:
                modules.append(m)
    modules_scope = ModulesScope(*modules)
    result = Expression(
        args.EXPRESSION,
        callable_objects=modules_scope.get_callable_objects(),
        constants=modules_scope.get_constants()
    ).execute()
    if console_mod:
        print(result)
    else:
        return result


if __name__ == '__main__':
    main()

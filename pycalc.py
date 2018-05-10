#!/usr/bin/env python3

from moduleloader import ModulesScope
from calcexpression import Expression
import argparse


if __name__ == '__main__':
    modules = ['builtins', 'math']
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
    print(result)

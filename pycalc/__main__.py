#!/usr/bin/env python3


def main():
    from pycalc.moduleloader import ModulesScope
    from pycalc.calcexpression import Expression
    import argparse

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


if __name__ == '__main__':
    main()

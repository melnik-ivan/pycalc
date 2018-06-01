"""
This module provides dynamic import functionality.
"""
from collections import namedtuple

Callable = namedtuple('Callable', 'pattern execute')
Constant = namedtuple('Constant', 'pattern value')


class ModuleLoader:
    """
    Provides access to constants and callable objects of corresponding module.
    """
    def __init__(self, module, callable_constructor=Callable, constant_constructor=Constant):
        self._callable_constructor = callable_constructor
        self._constant_constructor = constant_constructor
        self._callable_objects = []
        self._constants = []
        self._module = None
        self.load_module(module)

    def load_module(self, module):
        """
        Loads all constants and callable objects from module.
        """
        self._module = __import__(module)
        for key, value in self._module.__dict__.items():
            if callable(value):
                self._callable_objects.append(self._callable_constructor(key, value))
            else:
                self._constants.append(self._constant_constructor(key, value))

    def get_constants(self):
        """
        Returns list of constants.
        """
        return list(self._constants)

    def get_callable_objects(self):
        """
        Returns list of callable objects.
        """
        return list(self._callable_objects)


class ModulesScope:
    """
    Provides access to constants and callable objects of corresponding modules.
    """
    def __init__(self, *modules, module_loader=ModuleLoader):
        self._modules = [module_loader(m) for m in modules]
        self._constants = []
        self._callable_objects = []
        self.gen_scope()

    def gen_scope(self):
        """
        Loads all constants and callable objects from all modules.
        """
        for module in reversed(self._modules):
            for cst in module.get_constants():
                if cst not in self._constants:
                    self._constants.append(cst)
            for clb in module.get_callable_objects():
                if clb not in self._callable_objects:
                    self._callable_objects.append(clb)

    def get_constants(self):
        """
        Returns sorted by name length (longest first) list of constants.
        """
        return sorted(self._constants, key=lambda x: len(x.pattern), reverse=True)

    def get_callable_objects(self):
        """
        Returns sorted by name length (longest first) list of callable objects.
        """
        return sorted(self._callable_objects, key=lambda x: len(x.pattern), reverse=True)


BUILT_INS = ModuleLoader('builtins')

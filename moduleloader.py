from calcexpression import Callable, Constant


class ModuleLoader:
    def __init__(self, module, callable_constructor=Callable, constant_constructor=Constant):
        self._callable_constructor = callable_constructor
        self._constant_constructor = constant_constructor
        self._callable_objects = []
        self._constants = []
        self._module = None
        self.load_module(module)

    def load_module(self, module):
        self._module = __import__(module)
        for k, v in self._module.__dict__.items():
            if callable(v):
                self._callable_objects.append(self._callable_constructor(k, v))
            else:
                self._constants.append(self._constant_constructor(k, v))

    def get_constants(self):
        return list(self._constants)

    def get_callable_objects(self):
        return list(self._callable_objects)


class ModulesScope:
    def __init__(self, modules, module_loader=ModuleLoader):
        self._modules = [module_loader(m) for m in modules]
        self._constants = []
        self._callable_objects = []
        self.gen_scope()

    def gen_scope(self):
        for module in reversed(self._modules):
            for cst in module.get_constants():
                if cst not in self._constants:
                    self._constants.append(cst)
            for clb in module.get_callable_objects():
                if clb not in self._callable_objects:
                    self._callable_objects.append(clb)

    def get_constants(self):
        return list(self._constants)

    def get_callable_objects(self):
        return list(self._callable_objects)


if __name__ == '__main__':
    m = ModulesScope(('math', 'sys', 'builtins'))
    print(m.get_constants())


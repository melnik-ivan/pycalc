from calcexpression import Callable, Constant


class ModuleLoader:
    def __init__(self, module, callable_constructor=Callable, constant_constructor=Constant):
        self.callable_constructor = callable_constructor
        self.constant_constructor = constant_constructor
        self.module = None
        self.name_space = set()
        self.load_module(module)

    def load_module(self, module):
        self.module = __import__(module)
        self.name_space = set(filter(lambda x: not x.startswith('_'), dir(self.module)))

    def __getitem__(self, item):
        if item not in self.name_space:
            raise KeyError
        else:
            res = self.module.__dict__[item]
            if callable(res):
                return self.callable_constructor(item, res)
            else:
                return self.constant_constructor(item, res)


class ModulesScope:
    def __init__(self, modules, module_loader=ModuleLoader):
        self.modules = [module_loader(m) for m in modules]
        self.name_space = set()
        for mod in self.modules:
            self.name_space.update(mod.name_space)

    def __getitem__(self, item):
        if item not in self.name_space:
            raise KeyError
        else:
            for m in self.modules:
                try:
                    return m[item]
                except KeyError:
                    pass
            raise KeyError


if __name__ == '__main__':
    m = ModulesScope(('math', 'sys'))
    print(m['pi'])
    print(m['argv'])

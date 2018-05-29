import sys


class PyCalcSyntaxError(BaseException):
    def __init__(self, message="", *args, **kwargs):
        self.message = message
        super().__init__(*args, **kwargs)


def exceptions_handler(func):
    def wrapper(*args, **kwargs):
        result = ''
        try:
            result = func(*args, **kwargs)
        except PyCalcSyntaxError as error:
            print("ERROR: {}".format(error.message))
            sys.exit(2)
        except:
            print("ERROR: unexpected error")
            sys.exit(2)
        return result
    return wrapper

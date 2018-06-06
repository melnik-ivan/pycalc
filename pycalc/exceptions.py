"""
Provides exception and handlers to catch and display errors for
end-user.
"""
import sys
from functools import wraps


class PyCalcSyntaxError(Exception):
    """
    Pycalc exception with message attribute.
    """
    def __init__(self, message, *args, **kwargs):
        self.message = message
        super().__init__(*args, **kwargs)


def exceptions_handler(func):
    """
    Decorator for handling exceptions while pycalc is used as
    console utility.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        """
        Provides exceptions handling.
        """
        result = ''
        try:
            result = func(*args, **kwargs)
        except PyCalcSyntaxError as error:
            print("ERROR: {}".format(error.message))
            sys.exit(2)
        except ZeroDivisionError:
            print("ERROR: zero division error")
            sys.exit(2)
        except RecursionError:
            print("ERROR: the expression is too long")
            sys.exit(2)
        return result
    return wrapper

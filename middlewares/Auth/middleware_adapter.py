from django.utils.decorators import decorator_from_middleware_with_args

from .middleware import MiddlewareWithLogger


def get_access_controller(middleware=MiddlewareWithLogger):
    """
Decorator function that returns a decorator created from the given middleware class.

:param middleware: The middleware class to create the decorator from. Defaults to MiddlewareWithLogger.
:return: The decorator created from the middleware class.
"""
    return decorator_from_middleware_with_args(middleware)

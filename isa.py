"""constants to define the execution state for a notebook document.

## note

all of the doctests are scoped for a `doctest` invocation

    >>> import isa
    >>> assert isa.MODULE and not (isa.SCRIPT or isa.INTERACTIVE)
    >>> assert isa.MODULE and isa.FILE and not isa.MAIN
"""

from abc import ABCMeta
from functools import wraps
from inspect import currentframe, getouterframes

__all__ = "MAIN", "FILE", "INTERACTIVE", "SCRIPT", "MODULE"


def get_last_module():
    """the execution is determined for module calling a method

    inside classes and functions the local and global scopes are different.
    we walk the outer frames until we discovered the module where the
    frame is referenced. it is best to use this method in the top level of a module.
    """

    for frame in getouterframes(currentframe()):
        if frame.frame.f_locals is frame.frame.f_globals:
            return frame.frame


def _default_globals(callable):
    @wraps(callable)
    def default(globals=None):
        if globals is None:
            globals = get_last_module().f_globals
        return callable(globals)

    return default


# the state __name__ and __file__ are our primary conditions for execution state


@_default_globals
def is_main(globals=None):
    """determine if the globals name is main

    >>> assert not is_main()"""
    return globals.get("__name__") == "__main__"


@_default_globals
def is_file(globals=None):
    """determine if the globals contain a source file name

    >>> assert is_file()"""
    return bool(globals.get("__file__"))


@_default_globals
def is_interactive(globals=None):
    """determine if the globals are running as an interactive notebook

    >>> assert not is_interactive()"""
    return is_main(globals) and not is_file(globals)


@_default_globals
def is_module(globals=None):
    """determine if the globals are running as an imported module

    >>> assert is_module()"""
    return not is_main(globals) and is_file(globals)


@_default_globals
def is_script(globals=None):
    """determine if the globals are running from a command line script

    >>> assert not is_script()"""
    return is_main(globals) and is_file(globals)


class State(ABCMeta):
    """base type for execution state flags"""

    def __bool__(cls, level=1):
        return cls.predicate(get_last_module().f_globals)

    def __str__(cls):
        return str(bool(cls))

    def __or__(a, b):
        return a or b

    def __ror__(b, a):
        return a or b

    def __and__(a, b):
        return a and b

    def __rand__(b, a):
        return b and a


class MAIN(metaclass=State):
    """>>> assert not MAIN"""

    @classmethod
    def predicate(cls, globals):
        return is_main(globals)


class FILE(metaclass=State):
    """>>> assert FILE"""

    @classmethod
    def predicate(cls, globals):
        return bool(is_file(globals))


# the execution states are secondary combinations of __name__ and __file__ states


class INTERACTIVE(metaclass=State):
    """>>> assert not INTERACTIVE"""

    @classmethod
    def predicate(cls, globals):
        return is_interactive(globals)


class SCRIPT(metaclass=State):
    """>>> assert not SCRIPT"""

    @classmethod
    def predicate(cls, globals):
        return is_script(globals)


class MODULE(metaclass=State):
    """>>> assert MODULE"""

    @classmethod
    def predicate(cls, globals):
        return is_module(globals)


if SCRIPT:
    print(
        f"""interactive: {INTERACTIVE}
module: {MODULE}
script: {SCRIPT}"""
    )
elif MODULE:
    from subprocess import check_output

    __test__ = dict(
        test_script=f""">>> print(check_output(["python", "{__file__}"]).decode().rstrip())
interactive: False
module: False
script: True""",
        test_higher_conditons=""">>> assert not (MAIN | SCRIPT)
    >>> assert not MAIN & (not SCRIPT) & (not MAIN)
    >>> assert MODULE & (not MAIN) & FILE """,
    )

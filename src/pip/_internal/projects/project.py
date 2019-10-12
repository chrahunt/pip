from functools import wraps
from weakref import WeakKeyDictionary

from pip._internal.projects.base import ProjectInterface
from pip._internal.utils.typing import MYPY_CHECK_RUNNING

if MYPY_CHECK_RUNNING:
    from typing import Dict

    from pip._internal.projects.base import BaseProject


def if_not_implemented(prepare):
    """Decorator that calls `prepare` and then retries
    the decorated function.
    """
    def function_acceptor(fn):
        def wrapper(self, *args, **kwargs):
            try:
                return fn(self, *args, **kwargs)
            except NotImplementedError:
                prepare(self)
            return wrapper(self, *args, **kwargs)

        return wraps(fn)(wrapper)
    return function_acceptor


class checked_property(object):
    """Check that return value is always the same.
    """
    def __init__(self, fn):
        self._fn = fn
        self._fn_name = fn.__name__
        self._objs = WeakKeyDictionary()

    def __get__(self, obj, cls):
        if obj is None:
            return self
        value = self._fn(obj)
        previous_value = (
            self._objs
                .setdefault(obj, {})
                .setdefault(self._fn_name, value)
        )
        if value != previous_value:
            raise RuntimeError(
                "Output from {!r}.{} does not match previous. "
                "Old: {!r}; New: {!r}".format(
                    obj, self._fn_name, value, previous_value
                )
            )
        return value


class Project(ProjectInterface):
    """
    A ProjectInterface that delegates to an internal concrete project instance.

    If the internal project cannot provide the requested information, then
    it is prepared, yielding a new project which is then queried.
    """
    def __init__(self, project):
        # type: (BaseProject) -> None
        self._project = project
        self._data = {}  # type: Dict[str, str]
        self._states = [self._project]

    def _prepare(self):
        """Prepare the contained project, yielding a new project which should
        hopefully be able to provide the requested information.
        """
        self._project = self._project.prepare()
        self._states.append(self._project)

    def __repr__(self):
        states = []
        for state in self._states:
            states.append(repr(state))
        return 'Project({})'.format(' -> '.join(states))

    prepared = if_not_implemented(_prepare)

    @checked_property
    @prepared
    def name(self):
        return self._project.name

    @checked_property
    @prepared
    def dependencies(self):
        return self._project.dependencies

    @checked_property
    @prepared
    def version(self):
        return self._project.version

    @prepared
    def install(self, scheme):
        return self._project.install(scheme)

    @prepared
    def uninstall(self):
        return self._project.uninstall()

    @prepared
    def save_sdist(self):
        return self._project.save_sdist()

    @prepared
    def save_wheel(self):
        return self._project.save_wheel()

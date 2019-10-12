from functools import wraps

from pip._internal.projects.base import ProjectInterface
from pip._internal.utils.typing import MYPY_CHECK_RUNNING

if MYPY_CHECK_RUNNING:
    from typing import Dict

    from pip._internal.projects.base import BaseProject


def if_not_implemented(prepare):
    def function_acceptor(fn):
        def wrapper(self, *args, **kwargs):
            try:
                return fn(self, *args, **kwargs)
            except NotImplementedError:
                prepare(self)
            return wrapper(self, *args, **kwargs)

        return wraps(fn)(wrapper)
    return function_acceptor


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

    prepare = if_not_implemented(_prepare)

    @property
    @prepare
    def name(self):
        return self._project.name

    @property
    @prepare
    def dependencies(self):
        return self._project.dependencies

    @property
    @prepare
    def version(self):
        return self._project.version

    @prepare
    def install(self, scheme):
        return self._project.install(scheme)

    @prepare
    def uninstall(self):
        return self._project.uninstall()

    @prepare
    def save_sdist(self):
        return self._project.save_sdist()

    @prepare
    def save_wheel(self):
        return self._project.save_wheel()

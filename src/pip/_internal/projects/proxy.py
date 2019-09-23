from pip._internal.projects.base import ProjectInterface
from pip._internal.utils.typing import MYPY_CHECK_RUNNING

if MYPY_CHECK_RUNNING:
    from pip._internal.projects.base import BaseProject


class ProxyProject(ProjectInterface):
    """
    A ProjectInterface that delegates to an internal project instance.

    If the internal project cannot provide the requested information, then
    it is prepared, yielding a new project which is then queried.
    """
    def __init__(self, project):
        # type: (BaseProject) -> None
        self._project = project

    @property
    def name(self):
        try:
            return self._project.name
        except NotImplementedError:
            self._prepare()
        return self.name

    @property
    def dependencies(self):
        try:
            return self._project.dependencies
        except NotImplementedError:
            self._prepare()
        return self.dependencies

    @property
    def version(self):
        try:
            return self._project.version
        except NotImplementedError:
            self._prepare()
        return self.version

    def install(self, scheme):
        try:
            return self._project.install(scheme)
        except NotImplementedError:
            self._prepare()
        return self.install(scheme)

    def uninstall(self):
        try:
            return self._project.uninstall()
        except NotImplementedError:
            self._prepare()
        return self.uninstall()

    def save_sdist(self):
        try:
            return self._project.save_sdist()
        except NotImplementedError:
            self._prepare()
        return self.save_sdist()

    def save_wheel(self):
        try:
            return self._project.save_wheel()
        except NotImplementedError:
            self._prepare()
        return self.save_wheel()

    def _prepare(self):
        """Prepare the contained project, yielding a new project which should
        hopefully be able to provide the requested information.
        """
        self._project = self._project.prepare()

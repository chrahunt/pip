from pip._internal.projects.base import ProjectInterface
from pip._internal.utils.typing import MYPY_CHECK_RUNNING

if MYPY_CHECK_RUNNING:
    from pip._internal.projects.base import BaseProject


class ProxyProject(ProjectInterface):
    """
    Holds a BaseProject.
    """
    def __init__(self, project):
        # type: (BaseProject) -> None
        self._project = project

    @property
    def name(self):
        try:
            return self._project.name
        except NotImplementedError:
            self._advance()
        return self.name

    @property
    def dependencies(self):
        try:
            return self._project.dependencies
        except NotImplementedError:
            self._advance()
        return self.dependencies

    @property
    def version(self):
        try:
            return self._project.version
        except NotImplementedError:
            self._advance()
        return self.version

    @property
    def metadata(self):
        try:
            return self._project.metadata
        except NotImplementedError:
            self._advance()
        return self.metadata

    def install(self, scheme):
        try:
            return self._project.install(scheme)
        except NotImplementedError:
            self._advance()
        return self.install(scheme)

    def uninstall(self):
        try:
            return self._project.uninstall()
        except NotImplementedError:
            self._advance()
        return self.uninstall()

    def save_sdist(self):
        try:
            return self._project.save_sdist()
        except NotImplementedError:
            self._advance()
        return self.save_sdist()

    def save_wheel(self):
        try:
            return self._project.save_wheel()
        except NotImplementedError:
            self._advance()
        return self.save_wheel()

    def _advance(self):
        self._project = next(self._project)

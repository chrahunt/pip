"""Context represents configuration and services that are needed by all
projects.

When a project is prepared it creates another project. These utilities are
to help reduce the boilerplate required to provide the context to the newly-
instantiated project.
"""

from pip._internal.projects.base import BaseProject
from pip._internal.utils.typing import MYPY_CHECK_RUNNING

if MYPY_CHECK_RUNNING:
    from pip._internal.projects.config import ProjectConfig
    from pip._internal.projects.services import ProjectServices


class ProjectContext(object):
    """"""
    def __init__(self, config, services):
        # type: (ProjectConfig, ProjectServices) -> None
        super(ProjectContext, self).__init__()
        self.config = config
        self.services = services


class ProjectWithContext(ProjectContext, BaseProject):
    """Helper class to reduce code needed to provide context to a new
    class.

    super(T, self).__init__(ctx) sets `config` and `services`.
    """
    def __init__(self, ctx):
        # type: (ProjectContext) -> None
        super(ProjectWithContext, self).__init__(
            ctx.config, ctx.services,
        )

    def create(self, cls, *args, **kwargs):
        # type: (...) -> ...
        return cls(self, *args, **kwargs)

from pip._internal.projects.base import ProjectInterface
from pip._internal.projects.config import ProjectConfig
from pip._internal.projects.projects import ProjectContextProvider
from pip._internal.projects.services import ProjectServices


class ProjectFactory(object):
    """
    Does some of the work of
    - local_resolve.Resolver
    - operations.prepare.Preparer

    to initialize a project based on something which may represent:
    1. remote link
    2. local directory
    3. installed distribution

    There's some overlap between this and the Candidates returned by
    PackageFinder, need to identify what that is.
    """
    def __init__(self, config, services):
        # type: (ProjectConfig, ProjectServices) -> None
        self._root = ProjectContextProvider.from_info(config, services)

    def from_requirement(
        self,
        req,               # type: str
        constraint=False,  # type: bool
        editable=False,    # type: bool
    ):
        # type: (...) -> ProjectInterface
        """
        Given a requirement, construct a project for it.
        """
        # TODO: i.e. pip._internal.req.constructors
        pass

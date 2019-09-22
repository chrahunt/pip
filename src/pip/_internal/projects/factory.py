import os

from pip._internal.models.requirement import ParsedRequirement
from pip._internal.projects.base import ProjectInterface
from pip._internal.projects.config import ProjectConfig
from pip._internal.projects.projects import (
    ProjectContextProvider,
)
from pip._internal.projects.registry import ProjectTypeRegistry, all_projects
from pip._internal.projects.traits import (
    archive,
    directory,
    editable,
    local,
    named,
    remote,
    unnamed,
    vcs,
    wheel,
)
from pip._internal.projects.services import ProjectServices
from pip._internal.utils.filetypes import ARCHIVE_EXTENSIONS


class ProjectFactory(object):
    """
    Does some of the work of
    - local_resolve.Resolver
    - operations.prepare.Preparer

    to initialize a project based on something which may represent:
    1. remote link
    2. local directory
    3. installed distribution
    """
    def __init__(self, config, services):
        # type: (ProjectConfig, ProjectServices) -> None
        self._root = ProjectContextProvider.from_info(config, services)
        self._registry = ProjectTypeRegistry.from_projects(all_projects())

    def from_requirement(
        self,
        req,  # type: ParsedRequirement
    ):
        # type: (...) -> ProjectInterface
        """
        Given a requirement, construct a project for it.
        """
        if not req.parts.link:
            raise ValueError("Only requirements with links are valid!")

        traits = []
        if (
            req.parts.link.scheme == 'file' or '+file' in req.parts.link.scheme
        ):
            traits.append(local)
            if os.path.isdir(req.parts.link.file_path):
                traits.append(directory)
        else:
            traits.append(remote)

        if req.editable:
            traits.append(editable)

        if req.parts.requirement is not None:
            traits.append(named)
        else:
            traits.append(unnamed)

        if '+' in req.parts.link.scheme:
            traits.append(vcs)

        if req.parts.link.is_wheel:
            traits.append(wheel)
        elif req.parts.link.ext in ARCHIVE_EXTENSIONS:
            # XXX: Maybe we could be less-strict here.
            traits.append(archive)

        # TODO: sdist

        try:
            project_cls = self._registry[traits]
        except KeyError:
            raise RuntimeError(
                "No class found for {!r}".format(traits)
            )

        return project_cls.from_req(req)

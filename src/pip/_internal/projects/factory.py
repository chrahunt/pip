"""Provides the main interface for constructing Project instances, given a
ParsedRequirement.
"""

import os

from pip._internal.models.requirement import ParsedRequirement
from pip._internal.projects.base import ProjectInterface
from pip._internal.projects.config import ProjectConfig
from pip._internal.projects.projects import ProjectContext
from pip._internal.projects.proxy import ProxyProject
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
    Constructs Projects of the appropriate type given a requirement.

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
        self._root = ProjectContext(config, services)
        self._registry = ProjectTypeRegistry.from_projects(all_projects())

    def from_requirement(
        self,
        req,  # type: ParsedRequirement
    ):
        # type: (...) -> ProjectInterface
        """
        Given a requirement, construct a project for it.

        :raises RuntimeError: if
        """
        # We actually return ProxyProject instances, so that the returned
        # objects are more flexible.

        # We don't support "abstract" requirements - the requirement must have
        # been resolved to some concrete candidate, either explicitly by the
        # user or as the result of an index request.
        if not req.parts.link:
            raise ValueError("Parsed requirements must have links!")

        # We map the parsed requirement to a set of traits, which is used as a
        # key to locate the correct type in the project registry.
        traits = []
        if (
            # Generic file URL
            req.parts.link.scheme == 'file' or
            # VCS file URL
            '+file' in req.parts.link.scheme
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
        # TODO: sdist - this is important because it will contain name/version
        #  information that will allow us to avoid downloading anything.
        elif req.parts.link.ext in ARCHIVE_EXTENSIONS:
            # XXX: Maybe we could be less-strict here and consider it as a
            #  "file"
            traits.append(archive)

        try:
            project_cls = self._registry[traits]
        except KeyError:
            raise ValueError(
                "No class found for {!r}".format(traits)
            )

        # The class itself is actually responsible for going from a parsed
        # requirement to the project instance.
        initial_project = project_cls.from_req(req)
        return ProxyProject(initial_project)

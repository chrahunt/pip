"""Utilities for keeping track of all the project types and providing
a mechanism for retrieving them based on traits (e.g. editable, unnamed, vcs).
"""
from pip._internal.utils.typing import MYPY_CHECK_RUNNING

if MYPY_CHECK_RUNNING:
    from typing import Dict, Iterable, List, Type

    from typing_extensions import Protocol

    from pip._internal.models.requirement import ParsedRequirement
    from pip._internal.projects.base import BaseProject

    class ConstructibleProject(Protocol):
        """A type which provides `traits` (used as a key for locating the type)
        as well as a method for generating a project from a parsed requirement.
        """
        traits = []  # type: List[str]

        @classmethod
        def from_req(cls, req):
            # type: (ParsedRequirement) -> BaseProject
            ...


_projects = []  # type: List[Type[ConstructibleProject]]


def register(cls):
    # type: (Type[ConstructibleProject]) -> Type[ConstructibleProject]
    """Use as a decorator on project classes that may be used by initial input
    requirements (either from the user or as a dependency.

    The argument type enforces that the class provides `traits`.
    """
    _projects.append(cls)
    return cls


def all_projects():
    # type: () -> List[Type[ConstructibleProject]]
    """Returns a list of all registered project types.
    """
    return list(_projects)


def _make_key(traits):
    # type: (Iterable[str]) -> str
    return '-'.join(sorted(traits))


class ProjectTypeRegistry(object):
    """Tracks types and maps a set of traits to a concrete type.
    """
    def __init__(self, projects):
        # type: (Dict[str, Type[ConstructibleProject]]) -> None
        self._types = projects

    @classmethod
    def from_projects(cls, projects):
        # type: (List[Type[ConstructibleProject]]) -> ProjectTypeRegistry
        result = {}
        for project in projects:
            key = _make_key(project.traits)
            result[key] = project
        return ProjectTypeRegistry(result)

    def __getitem__(self, key_parts):
        # type: (List[str]) -> Type[ConstructibleProject]
        """Given a set of traits, return the associated concrete type.
        """
        key = _make_key(key_parts)
        return self._types[key]

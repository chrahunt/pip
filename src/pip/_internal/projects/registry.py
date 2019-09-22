"""Keeps track of types.
"""
from pip._internal.utils.typing import MYPY_CHECK_RUNNING

if MYPY_CHECK_RUNNING:
    from typing import Any, Dict, List


_projects = []


def input_project(*traits):
    """Mark a project as valid for input.
    """
    def cls_handler(cls):
        cls.traits = traits
        _projects.append(cls)
        return cls

    return cls_handler


def all_projects():
    # type: () -> List
    return list(_projects)


def type_key(traits):
    # type: (List[str]) -> str
    return '-'.join(sorted(traits))


class ProjectTypeRegistry(object):
    """Tracks types and maps input traits associated with a
    requirement to a concrete type.
    """
    def __init__(self, projects):
        # type: (Dict[str, ...]) -> None
        self._types = projects

    @classmethod
    def from_projects(cls, projects):
        # type: (List) -> ProjectTypeRegistry
        result = {}
        for project in projects:
            key = type_key(project.traits)
            result[key] = project
        return ProjectTypeRegistry(result)

    def __getitem__(self, item):
        # type: (List[str]) -> Any
        key = type_key(item)
        return self._types[key]

from pip._internal.utils.typing import MYPY_CHECK_RUNNING

if MYPY_CHECK_RUNNING:
    from typing import Dict, List


class ProjectInterface(object):
    @property
    def name(self):
        # type: () -> str
        """
        Name of the project.
        """
        raise NotImplementedError()

    @property
    def version(self):
        # type: () -> str
        raise NotImplementedError()

    @property
    def dependencies(self):
        # type: () -> List[str]
        raise NotImplementedError()

    # TODO: Identify the specific parts of the metadata required by clients
    #  and break this up.
    @property
    def metadata(self):
        """
        Return relevant metadata for this project.

        If anything expensive is done to do this calculation (like
        calling prepare_metadata_for_build_wheel) then it should be cached.
        """
        raise NotImplementedError()

    @property
    def installed(self):
        return False

    def is_compatible(self, state):
        # type: (...) -> bool
        """
        Return whether the project is compatible according to the provided
        state information (containing e.g. Python version, platform). We take
        state instead of deriving it internally because this can also be used
        to download for a different platform than the current one.

        :raises NotImplementedError - in the event that we don't know enough
          to say conclusively that we're compatible.
        """

    def install(self, scheme):
        # type: (Dict) -> None
        """
        Installs the project using the provided scheme.
        """
        raise NotImplementedError()

    def uninstall(self):
        # type: () -> None
        """
        Uninstalls the project.
        """
        raise NotImplementedError()

    def save_sdist(self):
        raise NotImplementedError()

    def save_wheel(self):
        raise NotImplementedError()


class BaseProject(ProjectInterface):
    def __next__(self):
        # type: () -> BaseProject
        ...

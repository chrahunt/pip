import os
from collections import namedtuple

from pip._internal.download import unpack_file_url
from pip._internal.projects.base import BaseProject
from pip._internal.pyproject import load_pyproject_toml
from pip._internal.utils.temp_dir import TempDirectory
from pip._internal.utils.typing import MYPY_CHECK_RUNNING
from pip._internal.wheel import Wheel

if MYPY_CHECK_RUNNING:
    from typing import Dict, List, Optional, Tuple

    from pip._internal.projects.config import ProjectConfig
    from pip._internal.projects.services import ProjectServices
    from pip._internal.models.link import Link


class ProjectContextProvider(object):
    def __init__(self, source):
        # type: (ProjectContextProvider) -> None
        super(ProjectContextProvider, self).__init__()
        self.config = source.config  # type: ProjectConfig
        self.services = source.services  # type: ProjectServices

    @classmethod
    def from_info(cls, config, services):
        # type: (ProjectConfig, ProjectServices) -> ProjectContextProvider
        """Bootstrap a context provider from its component parts."""
        FakeContextProvider = namedtuple(
            'FakeContextProvider',
            ['config', 'services'],
        )
        return cls(FakeContextProvider(config, services))


class ProjectWithContext(ProjectContextProvider, BaseProject):
    def __init__(self, ctx):
        # type: (ProjectContextProvider) -> None
        super(ProjectWithContext, self).__init__(ctx)


def download(downloader, source):
    # type: (..., Link) -> str
    # TODO: Globally manage temporary directory.
    temp_dir = TempDirectory(kind="download")
    temp_dir.create()
    output_path = os.path.join(temp_dir.path, source.filename)
    downloader(source, output_path)
    return output_path


class LocalArchive(ProjectWithContext):
    def __init__(self, ctx, link):
        # type: (ProjectContextProvider, Link) -> None
        super(LocalArchive, self).__init__(ctx)
        self._link = link

    def __next__(self):
        # type: () -> BaseProject
        # TODO: Unpack the archive and return UnpackedSources.
        # TODO: Determine how an archive, as an unnamed requirement,
        #  currently provides a name for the pyproject_toml?
        #  - it doesn't provide a name, it provides an identifier which is
        #    only used for logging purposes.
        ...


class LocalEditableDirectory(BaseProject):
    pass


class LocalEditableLegacy(BaseProject):
    pass


class LocalEditableNamedVcs(BaseProject):
    pass


class LocalLegacyProject(ProjectWithContext):
    def __init__(self, ctx, source_directory):
        # type: (ProjectContextProvider, str) -> None
        super(LocalLegacyProject, self).__init__(ctx)
        self._source_directory = source_directory

    @property
    def name(self):
        # TODO: Derive from metadata.
        return

    @property
    def version(self):
        # TODO: Derive from metadata.
        return

    @property
    def metadata(self):
        # TODO: Call egg_info (req.req_install.InstallRequirement.run_egg_info)
        return

    def install(self, scheme):
        # type: (Dict) -> None
        # TODO: How to organize this so that it will fail with
        #  NotImplementedError if a wheel build would succeed?
        pass

    def __next__(self):
        # type: () -> BaseProject
        # TODO: If wheel is installed, build wheel
        # TODO: If that fails, or wheel is not installed,
        ...


class LocalModernProject(ProjectWithContext):
    def __init__(
        self,
        ctx,  # type: ProjectContextProvider
        source_directory,  # type: str
        pyproject_toml_data,  # type: Tuple[List[str], str, List[str]]
    ):
        # type: (...) -> None
        super(LocalModernProject, self).__init__(ctx)
        self._source_directory = source_directory
        # TODO: Populate like the rest of InstallRequirement.load_pyproject_toml

    @property
    def metadata(self):
        # TODO: if prepare_metadata_for_build_wheel is not implemented,
        #  raise NotImplementedError().
        # TODO: call prepare_metadata_for_build_wheel (
        #  req.req_install.InstallRequirement.prepare_pep517_metadata)
        # TODO: cache result
        return

    def __next__(self):
        # TODO: Build project into wheel
        return LocalWheel(self)


class LocalNamedVcs(BaseProject):
    pass


class LocalNonEditableDirectory(BaseProject):
    def __init__(self, ctx, source_directory):
        super(LocalNonEditableDirectory, self).__init__(ctx)
        self._source_directory = source_directory


class LocalSdist(BaseProject):
    def __init__(self, ctx, path):
        super(LocalSdist, self).__init__(ctx)
        self._path = path

    @property
    def name(self):
        return

    @property
    def version(self):
        return

    def save_sdist(self):
        # TODO: Copy sdist to provided directory.
        pass

    def __next__(self):
        # type: () -> BaseProject
        # TODO: Unpack into a temporary unpacked source directory.
        ...


class LocalUnnamedVcs(BaseProject):
    pass


class LocalWheel(ProjectWithContext):

    """
    A local wheel file provided by the user or downloaded from an index.
    """

    def __init__(self, parent, link):
        # type: (ProjectWithContext, Link) -> None
        """
        :param link: link to local wheel file
        """
        super(LocalWheel, self).__init__(parent)
        # Link to local wheel file.
        self._link = link
        self._wheel = Wheel(self._link.filename)

    @property
    def name(self):
        return self._wheel.name

    @property
    def version(self):
        return self._wheel.version

    @property
    def metadata(self):
        # XXX: We could extract the METADATA and other files from the wheel
        #  file without unpacking the whole thing.
        raise NotImplementedError()

    def is_compatible(self, state):
        # type: (...) -> bool
        pass

    def __next__(self):
        """
        Unpacks to UnpackedWheel.
        """
        # From: pip._internal.wheel.WheelBuilder.build.
        # TODO: Globally-manage temporary directories.
        source_dir = TempDirectory(kind="unpacked-wheel")
        source_dir.create()
        unpack_file_url(link=self._link, location=source_dir.path)
        return UnpackedWheel(self, source_dir.path)


class RemoteArchive(ProjectWithContext):
    def __init__(self, ctx, link):
        # type: (ProjectContextProvider, Link) -> None
        super(RemoteArchive, self).__init__(ctx)
        self._link = link

    def __next__(self):
        downloaded = download(self.services.download, self._link)
        return LocalArchive(self, Link(downloaded))


class RemoteEditableNamedVcs(BaseProject):
    pass


class RemoteNamedVcs(BaseProject):
    pass


class RemoteSdist(ProjectWithContext):
    def __init__(self, ctx, link):
        # type: (ProjectContextProvider, Link) -> None
        super(RemoteSdist, self).__init__(ctx)
        self._link = link

    @property
    def name(self):
        # XXX: Could derive from link, see pypa/pip#1689.
        raise NotImplementedError()

    @property
    def version(self):
        # XXX: Could derive from link, see pypa/pip#1689.
        raise NotImplementedError()

    def __next__(self):
        downloaded = download(self.services.download, self._link)
        return LocalSdist(self, Link(downloaded))


class RemoteUnnamedVcs(BaseProject):
    pass


class RemoteWheel(ProjectWithContext):
    def __init__(self, parent, link):
        # type: (ProjectWithContext, Link) -> None
        super(RemoteWheel, self).__init__(parent)
        self._link = link
        self._wheel = Wheel(self._link.filename)

    @property
    def name(self):
        return self._wheel.name

    @property
    def version(self):
        return self._wheel.version

    def is_compatible(self, state):
        # type: (...) -> bool
        # TODO: Derive compatibility from wheel tags and compare against
        #  state. If still compatible-looking then raise NotImplementedError
        #  so the wheel is downloaded.
        raise NotImplementedError()

    def __next__(self):
        # type: () -> BaseProject
        temp_dir = TempDirectory(kind="download")
        output_path = os.path.join(temp_dir.path, self._link.filename)
        self.services.download(self._link, output_path)
        return LocalWheel(self, Link(output_path))


class UnpackedSources(ProjectWithContext):
    def __init__(
        self,
        ctx,  # type: ProjectContextProvider
        source_directory,  # type: str,
        name=None,  # type: Optional[str]
    ):
        # type: (...) -> None
        super(UnpackedSources, self).__init__(ctx)
        self._source_directory = source_directory
        self._name = name

    @property
    def name(self):
        # We came from an unnamed requirement.
        if self._name is None:
            raise NotImplementedError()
        return self._name

    @property
    def _pyproject_toml_path(self):
        # type: () -> str
        # TODO: i.e. InstallRequirement.pyproject_toml_path
        return ''

    @property
    def _setup_py_path(self):
        # type: () -> str
        # TODO: i.e. InstallRequirement.setup_py_path
        return ''

    def __next__(self):
        # type: () -> BaseProject
        # From: InstallRequirement.load_pyproject_toml
        pyproject_toml_data = load_pyproject_toml(
            self.config.use_pep517,
            self._pyproject_toml_path,
            self._setup_py_path,
            self.name
        )

        if pyproject_toml_data is None:
            return LocalLegacyProject(self, self._source_directory)
        return LocalModernProject(
            self, self._source_directory, pyproject_toml_data
        )


class UnpackedWheel(ProjectWithContext):
    def __init__(self, parent, unpacked_dir):
        # type: (ProjectWithContext, str) -> None
        super(UnpackedWheel, self).__init__(parent)
        self._unpacked_dir = unpacked_dir

    @property
    def name(self):
        # type: () -> str
        # TODO: Use self.metadata.
        return ''

    @property
    def version(self):
        # type: () -> str
        # TODO: Use self.metadata.
        return ''

    @property
    def metadata(self):
        # TODO: Extract from self._unpacked_dir/*.dist-info/METADATA.
        return

    def install(self, scheme):
        # From: pip._internal.req.req_install.InstallRequirement.move_wheel_files.
        ...

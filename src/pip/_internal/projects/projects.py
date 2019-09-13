import os
import sys
from collections import namedtuple
from contextlib import contextmanager

from pip._vendor import six
from pip._vendor.pep517.wrappers import Pep517HookCaller

from pip._internal.download import unpack_file_url
from pip._internal.projects.base import BaseProject
from pip._internal.pyproject import load_pyproject_toml, make_pyproject_path
from pip._internal.utils.misc import (
    cached_property,
    call_subprocess,
    ensure_dir,
)
from pip._internal.utils.temp_dir import TempDirectory
from pip._internal.utils.typing import MYPY_CHECK_RUNNING
from pip._internal.utils.ui import open_spinner
from pip._internal.wheel import Wheel

if MYPY_CHECK_RUNNING:
    from typing import Any, Dict, List, Mapping, Optional, Tuple

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
        temp_dir = TempDirectory(kind="unpack")
        temp_dir.create()
        unpack_file_url(self._link, temp_dir.path)
        return UnpackedSources(self, temp_dir.path, str(self._link))


class LocalEditableDirectory(ProjectWithContext):
    def __init__(self, ctx, link):
        # type: (ProjectContextProvider, Link) -> None
        super(LocalEditableDirectory, self).__init__(ctx)
        self._link = link

    def __next__(self):
        # type: () -> BaseProject
        # TODO: Verifications and then return LocalEditableLegacy.
        ...


class LocalEditableLegacy(ProjectWithContext):
    def __init__(self, ctx, link):
        super(LocalEditableLegacy, self).__init__(ctx)
        self._link = link

    def install(self, scheme):
        # type: (Dict) -> None
        # TODO: i.e. InstallRequirement.install_editable
        ...


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

    @cached_property
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
        # TODO: If that fails, or wheel is not installed, then install directly.
        ...


class Pep517BackendHolder(object):
    def __init__(self, backend):
        # type: (Pep517HookCaller) -> None
        self._backend = backend

    @contextmanager
    def backend_operation(self, spin_message):
        # type: (str) -> Pep517HookCaller
        def runner(
            cmd,  # type: List[str]
            cwd=None,  # type: Optional[str]
            extra_environ=None  # type: Optional[Mapping[str, Any]]
        ):
            # type: (...) -> None
            with open_spinner(spin_message) as spinner:
                call_subprocess(
                    cmd,
                    cwd=cwd,
                    extra_environ=extra_environ,
                    spinner=spinner
                )

        with self._backend.subprocess_runner(runner):
            yield self._backend


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
        requires, backend, check = pyproject_toml_data
        self._requirements_to_check = check
        self._pyproject_requires = requires
        self._pep517_backend = Pep517HookCaller(
            self._source_directory, backend,
        )
        self._pep517_backend_holder = Pep517BackendHolder(self._pep517_backend)

    @property
    def metadata(self):
        # XXX: We may be able to avoid building a wheel here if the backend
        #  implements `prepare_metadata_for_build_wheel`, but per
        #  pypa/pep517#58, there is not a way to NOT build the wheel if the
        #  hook does not exist. For consistency we will always build the wheel.
        # XXX: Once the issue above is fixed we should try to invoke the hook
        #  and provide the metadata if possible.
        raise NotImplementedError()

    def __next__(self):
        # TODO:
        #  1. Create build environment
        #     (distributions.source.legacy.SourceDistribution
        #      .prepare_distribution_metadata)
        #  2. Do wheel build (wheel.WheelBuilder._build_one_pep517)
        #  3. Return LocalWheel
        return


class LocalNamedVcs(BaseProject):
    pass


class LocalNonEditableDirectory(BaseProject):
    def __init__(self, ctx, source_directory):
        super(LocalNonEditableDirectory, self).__init__(ctx)
        self._source_directory = source_directory


class LocalSdist(ProjectWithContext):
    def __init__(self, ctx, path):
        super(LocalSdist, self).__init__(ctx)
        self._path = path

    @property
    def name(self):
        # XXX: Could derive from link, see pypa/pip#1689.
        raise NotImplementedError()

    @property
    def version(self):
        # XXX: Could derive from link, see pypa/pip#1689.
        raise NotImplementedError()

    def save_sdist(self):
        # TODO: Copy sdist to provided directory.
        raise NotImplementedError()

    def __next__(self):
        # type: () -> BaseProject
        temp_dir = TempDirectory(kind="unpack")
        temp_dir.create()
        unpack_file_url(self._path, temp_dir.path)
        return UnpackedSources(self, temp_dir.path, str(self._path))


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
        ctx,               # type: ProjectContextProvider
        source_directory,  # type: str
        source,            # type: str
        name=None,         # type: Optional[str]
        version=None,      # type: Optional[str]
    ):
        # type: (...) -> None
        """
        :param ctx: project context
        :param source_directory: the root of the unpacked project
            (which contains a setup.py or pyproject.toml)
        :param source: identifier for the origin of the requirement, for error
            reporting
        :param name: the official name of the requirement, if already
            determined
        :param version: the official version of the requirement, if already
            determined
        """
        super(UnpackedSources, self).__init__(ctx)
        self._source_directory = source_directory
        self._source = source
        self._name = name
        self._version = version

    @property
    def name(self):
        # type: () -> str
        # We came from an unnamed requirement.
        if self._name is None:
            raise NotImplementedError()
        return self._name

    @property
    def version(self):
        # type: () -> str
        if self._version is None:
            raise NotImplementedError()
        return self._version

    @property
    def _pyproject_toml_path(self):
        # type: () -> str
        return make_pyproject_path(self._source_directory)

    @cached_property
    def _setup_py_path(self):
        # type: () -> str
        # i.e. InstallRequirement.setup_py_path but without the complication
        # of editable VCS requirements (with subdirectory)
        path = os.path.join(self._source_directory, 'setup.py')

        # Python2 __file__ should not be unicode
        if six.PY2 and isinstance(path, six.text_type):
            path = path.encode(sys.getfilesystemencoding())

        return path

    def __next__(self):
        # type: () -> BaseProject
        # From: InstallRequirement.load_pyproject_toml
        pyproject_toml_data = load_pyproject_toml(
            self.config.use_pep517,
            self._pyproject_toml_path,
            self._setup_py_path,
            self._source,
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

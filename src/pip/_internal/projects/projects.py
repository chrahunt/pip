"""Projects representing the various states that a package may be in, along
with implementations of ProjectInterface methods/properties to query their
information.

When not immediately available, projects will generally acquire their
information lazily.

If a previous state of the project could have acquired some information that
would have been used in resolution, it will pass that information on as a
Requirement. Later states of the project should explicitly validate that
information against newly-acquired information. For example, validating an
`#egg=`-provided value against the name in the metadata output from
`python setup.py egg_info`.
"""

import os
import sys
from contextlib import contextmanager

from pip._vendor import six
from pip._vendor.pep517.wrappers import Pep517HookCaller
from pip._vendor.packaging.requirements import Requirement

from pip._internal.build_env import NoOpBuildEnvironment
from pip._internal.commands.install import is_wheel_installed
from pip._internal.download import unpack_file_url
from pip._internal.operations.generate_metadata import _generate_metadata_legacy
from pip._internal.projects.base import BaseProject
from pip._internal.projects.context import ProjectContext, ProjectWithContext
from pip._internal.projects.registry import register
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
from pip._internal.pyproject import load_pyproject_toml, make_pyproject_path
from pip._internal.req.req_install import get_dist
from pip._internal.utils.misc import cached_property
from pip._internal.utils.packaging import get_metadata
from pip._internal.utils.subprocess import call_subprocess
from pip._internal.utils.temp_dir import TempDirectory
from pip._internal.utils.typing import MYPY_CHECK_RUNNING
from pip._internal.utils.ui import open_spinner
from pip._internal.wheel import Wheel

if MYPY_CHECK_RUNNING:
    from typing import (
        Any, Callable, Dict, Iterator, List, Mapping, Optional, Tuple, Union,
    )

    from pip._internal.models.link import Link
    from pip._internal.models.requirement import ParsedRequirement

    Downloader = Callable[[Link, str], None]


def download(downloader, source):
    # type: (Downloader, Link) -> str
    # TODO: Globally manage temporary directory.
    temp_dir = TempDirectory(kind="download")
    output_path = os.path.join(temp_dir.path, source.filename)
    downloader(source, output_path)
    return output_path


@register
class LocalArchive(ProjectWithContext):

    traits = [local, archive]

    def __init__(self, ctx, link):
        # type: (ProjectContext, Link) -> None
        super(LocalArchive, self).__init__(ctx)
        self._link = link

    @classmethod
    def from_req(cls, ctx, req):
        # type: (ProjectContext, ParsedRequirement) -> LocalArchive
        return cls(ctx, req.parts.link)

    def prepare(self):
        # type: () -> UnpackedSources
        temp_dir = TempDirectory(kind="unpack")
        unpack_file_url(self._link, temp_dir.path)
        return UnpackedSources(self, temp_dir.path, str(self._link))


@register
class LocalEditableDirectory(ProjectWithContext):

    traits = [local, editable, directory]

    def __init__(self, ctx, link):
        # type: (ProjectContext, Link) -> None
        super(LocalEditableDirectory, self).__init__(ctx)
        self._link = link

    @classmethod
    def from_req(cls, req):
        # type: (ParsedRequirement) -> LocalEditableDirectory
        raise NotImplementedError('TODO')

    def prepare(self):
        # type: () -> LocalEditableLegacy
        # TODO: Verifications and then return LocalEditableLegacy.
        raise NotImplementedError('TODO')


class LocalEditableLegacy(ProjectWithContext):
    def __init__(
        self,
        ctx,       # type: ProjectContext
        link,      # type: Link
        req=None,  # type: Optional[Requirement]
    ):
        # type: (...) -> None
        super(LocalEditableLegacy, self).__init__(ctx)
        self._link = link
        self._req = req

    @property
    def name(self):
        # type: () -> str
        # TODO: Derive from metadata
        raise NotImplementedError('TODO')

    @property
    def version(self):
        # type: () -> str
        # TODO: Derive from metadata
        raise NotImplementedError('TODO')

    @property
    def dependencies(self):
        # type: () -> List[str]
        # TODO: Derive from metadata
        raise NotImplementedError('TODO')

    def install(self, scheme):
        # type: (Dict) -> None
        # TODO: i.e. InstallRequirement.install_editable
        raise NotImplementedError('TODO')


@register
class LocalEditableNamedVcs(ProjectWithContext):

    traits = [local, editable, named, vcs]

    def __init__(self, ctx, link, req):
        # type: (ProjectContext, Link, Requirement) -> None
        super(LocalEditableNamedVcs, self).__init__(ctx)
        self._link = link
        self._req = req

    @property
    def name(self):
        # type: () -> str
        return self._req.name

    def prepare(self):
        # type: () -> LocalEditableLegacy
        path = self._link.file_path
        # TODO: Handle subdirectory.
        setup_py_path = os.path.join(path, "setup.py")
        if not os.path.exists(setup_py_path):
            # TODO: More granular error.
            raise RuntimeError(
                "{} is not an editable project".format(
                    self._link.url,
                )
            )
        return LocalEditableLegacy(self, self._link, self._req)


class LocalLegacyProject(ProjectWithContext):
    def __init__(
        self,
        ctx,               # type: ProjectContext
        source_directory,  # type: str
        req=None,          # type: Optional[Requirement]
    ):
        # type: (...) -> None
        super(LocalLegacyProject, self).__init__(ctx)
        self._source_directory = source_directory
        self._req = req

    @property
    def name(self):
        # type: () -> str
        return self._metadata["Name"]

    @property
    def version(self):
        # type: () -> str
        return self._metadata["Version"]

    @property
    def dependencies(self):
        # type: () -> List[str]
        raise NotImplementedError('TODO')

    @cached_property
    def _metadata(self):
        metadata_directory = _generate_metadata_legacy(
            name=None,
            link=self._source_directory,
            setup_py_path=os.path.join(self._source_directory, 'setup.py'),
            isolated=self.config.isolated,
            editable=False,
            source_directory=self._source_directory,
            build_env=NoOpBuildEnvironment(),
        )

        dist = get_dist(metadata_directory)

        return get_metadata(dist)

    def prepare(self):
        # type: () -> Union[LocalLegacyNonWheelProject, LocalWheel]
        if not is_wheel_installed():
            return LocalLegacyNonWheelProject(self._source_directory, self._metadata)
        # TODO:
        #  1. Try to build a wheel
        #  2. If wheel build succeeds, return LocalWheel
        #  3. Otherwise, return LocalLegacyNonWheelProject
        raise NotImplementedError('TODO')


class LocalLegacyNonWheelProject(ProjectWithContext):
    def __init__(self, ctx, source_directory, metadata):
        # type: (ProjectContext, str, Dict)
        super(LocalLegacyNonWheelProject, self).__init__(ctx)
        self._source_directory = source_directory
        self._metadata = metadata

    @property
    def install(self, scheme):
        # type: (Dict) -> None
        # TODO: setup.py install
        raise NotImplementedError('TODO')


class Pep517BackendHolder(object):
    def __init__(self, backend):
        # type: (Pep517HookCaller) -> None
        self._backend = backend

    @contextmanager
    def backend_operation(self, spin_message):
        # type: (str) -> Iterator[Pep517HookCaller]
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
        ctx,                  # type: ProjectContext
        source_directory,     # type: str
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
        # TODO:
        #  1. self._pip517_backend.prepare_metadata_for_build_wheel(
        #       ..., _allow_fallback=False
        #     )
        #  2. If that fails, raise NotImplementedError()
        raise NotImplementedError()

    def prepare(self):
        # type: () -> LocalWheel
        # TODO:
        #  1. Create build environment
        #     (distributions.source.legacy.SourceDistribution
        #      .prepare_distribution_metadata)
        #  2. Do wheel build (wheel.WheelBuilder._build_one_pep517)
        #     1. If prepare_metadata_for_build_wheel ran/succeeded, then pass
        #        in the same metadata directory.
        #  3. Return LocalWheel
        raise NotImplementedError('TODO')


@register
class LocalNamedVcs(ProjectWithContext):

    traits = [local, named, vcs]

    def __init__(self, ctx, source_directory, name):
        # type: (ProjectContext, str, str) -> None
        super(LocalNamedVcs, self).__init__(ctx)
        self._source_directory = source_directory
        self._name = name


@register
class LocalNonEditableDirectory(ProjectWithContext):

    """
    e.g. pip install .
    """

    traits = [local, unnamed, directory]

    def __init__(self, ctx, source_directory):
        # type: (ProjectContext, Link) -> None
        super(LocalNonEditableDirectory, self).__init__(ctx)
        self._source_directory = source_directory

    @classmethod
    def from_req(cls, ctx, req):
        # type: (ProjectContext, ParsedRequirement) -> LocalNonEditableDirectory
        return cls(ctx, req.parts.link)

    def prepare(self):
        # type: () -> UnpackedSources
        temp_dir = TempDirectory(kind="unpack")
        unpack_file_url(self._source_directory, temp_dir.path)
        return UnpackedSources(self, temp_dir.path, str(self._source_directory))


class LocalSdist(ProjectWithContext):
    def __init__(self, ctx, path):
        # type: (ProjectContext, str) -> None
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
        # type: () -> None
        # TODO: Copy sdist to provided directory.
        raise NotImplementedError('TODO')

    def prepare(self):
        # type: () -> UnpackedSources
        temp_dir = TempDirectory(kind="unpack")
        unpack_file_url(self._path, temp_dir.path)
        return UnpackedSources(self, temp_dir.path, str(self._path))


@register
class LocalUnnamedVcs(ProjectWithContext):

    traits = [local, unnamed, vcs]

    def __init__(self, ctx):
        # type: (ProjectContext) -> None
        super(LocalUnnamedVcs, self).__init__(ctx)
        raise NotImplementedError('TODO')

    def prepare(self):
        # type: () -> Union[LocalLegacyProject, LocalModernProject]
        # TODO: Identify project type
        raise NotImplementedError('TODO')


@register
class LocalWheel(ProjectWithContext):

    traits = [local, wheel]

    """
    A local wheel file provided by the user or downloaded from an index.
    """

    def __init__(self, ctx, link):
        # type: (ProjectContext, Link) -> None
        """
        :param link: link to local wheel file
        """
        super(LocalWheel, self).__init__(ctx)
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
        raise NotImplementedError('TODO')

    def prepare(self):
        # type: () -> UnpackedWheel
        """
        Unpacks to UnpackedWheel.
        """
        # From: pip._internal.wheel.WheelBuilder.build.
        # TODO: Globally-manage temporary directories.
        source_dir = TempDirectory(kind="unpacked-wheel")
        source_dir.create()
        unpack_file_url(link=self._link, location=source_dir.path)
        return UnpackedWheel(self, source_dir.path)


@register
class RemoteArchive(ProjectWithContext):

    traits = [remote, archive]

    def __init__(self, ctx, link):
        # type: (ProjectContext, Link) -> None
        super(RemoteArchive, self).__init__(ctx)
        self._link = link

    def prepare(self):
        # type: () -> LocalArchive
        downloaded = download(self.services.download, self._link)
        return LocalArchive(self, Link(downloaded))


@register
class RemoteEditableNamedVcs(ProjectWithContext):

    traits = [remote, editable, named, vcs]

    def __init__(self, ctx):
        # type: (ProjectContext) -> None
        super(RemoteEditableNamedVcs, self).__init__(ctx)


@register
class RemoteNamedVcs(ProjectWithContext):

    traits = [remote, named, vcs]

    def __init__(self, ctx):
        # type: (ProjectContext) -> None
        super(RemoteNamedVcs, self).__init__(ctx)


class RemoteSdist(ProjectWithContext):
    def __init__(self, ctx, link):
        # type: (ProjectContext, Link) -> None
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

    def prepare(self):
        # type: () -> LocalSdist
        downloaded = download(self.services.download, self._link)
        return LocalSdist(self, Link(downloaded))


@register
class RemoteUnnamedVcs(BaseProject):

    traits = [remote, unnamed, vcs]


@register
class RemoteWheel(ProjectWithContext):

    traits = [remote, wheel]

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
        raise NotImplementedError('TODO')

    def prepare(self):
        # type: () -> LocalWheel
        temp_dir = TempDirectory(kind="download")
        output_path = os.path.join(temp_dir.path, self._link.filename)
        self.services.download(self._link, output_path)
        return LocalWheel(self, Link(output_path))


class UnpackedSources(ProjectWithContext):
    def __init__(
        self,
        ctx,               # type: ProjectContext
        source_directory,  # type: str
        source,            # type: str
        req=None,          # type: Optional[ParsedRequirement]
    ):
        # type: (...) -> None
        """
        :param ctx: project context
        :param source_directory: the root of the unpacked project
            (which contains a setup.py or pyproject.toml)
        :param source: identifier for the origin of the requirement, for error
            reporting
        :param req: the official name of the requirement, if already
            determined
        """
        super(UnpackedSources, self).__init__(ctx)
        self._source_directory = source_directory
        self._source = source
        self._req = req

    @property
    def name(self):
        # type: () -> str
        # i.e. we came from an unnamed requirement.
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

    def prepare(self):
        # type: () -> Union[LocalLegacyProject, LocalModernProject]
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
        raise NotImplementedError('TODO')

    @property
    def version(self):
        # type: () -> str
        # TODO: Use self.metadata.
        raise NotImplementedError('TODO')

    @property
    def _metadata(self):
        # TODO: Extract from self._unpacked_dir/*.dist-info/METADATA.
        raise NotImplementedError('TODO')

    def install(self, scheme):
        # TODO: From:
        #  pip._internal.req.req_install.InstallRequirement.move_wheel_files.
        raise NotImplementedError('TODO')

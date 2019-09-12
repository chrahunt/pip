import os

from pip._internal.download import unpack_file_url
from pip._internal.projects.base import BaseProject
from pip._internal.utils.temp_dir import TempDirectory
from pip._internal.utils.typing import MYPY_CHECK_RUNNING
from pip._internal.wheel import Wheel

if MYPY_CHECK_RUNNING:
    from pip._internal.models.link import Link


class BaseProjectWithInit(BaseProject):
    def __init__(self, parent):
        # type: (BaseProjectWithInit) -> None
        self.config = parent.config
        self.services = parent.services


class LocalWheel(BaseProjectWithInit):

    """
    A local wheel file provided by the user or downloaded from an index.
    """

    def __init__(self, parent, link):
        # type: (BaseProjectWithInit, Link) -> None
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
        # TODO: (optional) extracted from the wheel file without requiring
        #  unpacking.
        return

    def is_compatible(self, state):
        # type: (...) -> bool
        pass

    def __next__(self):
        """
        Unpacks to UnpackedWheel.
        """
        # From: pip._internal.wheel.WheelBuilder.build.
        # TODO: Globally-managed.
        source_dir = TempDirectory(kind="unpacked-wheel")
        source_dir.create()
        unpack_file_url(link=self._link, location=source_dir.path)
        return UnpackedWheel(self, source_dir.path)


class UnpackedWheel(BaseProjectWithInit):
    def __init__(self, parent, unpacked_dir):
        # type: (BaseProjectWithInit, str) -> None
        super(UnpackedWheel, self).__init__(parent)
        self._unpacked_dir = unpacked_dir

    @property
    def name(self):
        # TODO: Extract from METADATA.
        return

    @property
    def version(self):
        # TODO: Extract from METADATA.
        return

    def install(self, scheme):
        # From: pip._internal.req.req_install.InstallRequirement.move_wheel_files.
        ...


class RemoteNamedVcs(BaseProject):
    pass


class RemoteUnnamedVcs(BaseProject):
    pass


class RemoveArchive(BaseProject):
    def __init__(self, link):
        self._link = link

    def __next__(self):
        # TODO: Download and return LocalArchive.
        ...


class RemoteSdist(BaseProject):
    def __init__(self, link):
        self._link = link

    @property
    def name(self):
        # TODO: Derive from name of remote project.
        return

    @property
    def version(self):
        # TODO: Derive from name of remote project.
        return

    def __next__(self):
        # TODO: Download and return LocalSdist, similar to
        #  pip._internal.operations.prepare.Preparer.prepare_linked_requirement
        # One difficulty here is the integration of the download directory,
        # it would be simpler if we could always download to a temporary directory.
        ...


class RemoteWheel(BaseProjectWithInit):
    def __init__(self, parent, link):
        # type: (BaseProjectWithInit, Link) -> None
        super(RemoteWheel, self).__init__(parent)
        self._link = link

    @property
    def name(self):
        # TODO: Derive from wheel filename.
        return

    @property
    def version(self):
        # TODO: Derive from wheel filename.
        return

    def is_compatible(self, state):
        # type: (...) -> bool
        # TODO: Derive compatibility from wheel tags and compare against
        #  state.
        raise NotImplementedError()

    def __next__(self):
        # type: () -> BaseProject
        temp_dir = TempDirectory(kind="download")
        output_path = os.path.join(temp_dir.path, self._link.filename)
        self.services.download(self._link, output_path)
        return LocalWheel(self, output_path)


class RemoteEditableNamedVcs(BaseProject):
    pass


class LocalNonEditableDirectory(BaseProject):
    pass


class LocalSdist(BaseProject):
    pass


class LocalArchive(BaseProject):
    pass


class LocalEditableNamedVcs(BaseProject):
    pass


class LocalEditableDirectory(BaseProject):
    pass


class LocalEditableLegacy(BaseProject):
    pass


class UnpackedSources(BaseProject):
    pass


class LocalUnnamedVcs(BaseProject):
    pass


class LocalNamedVcs(BaseProject):
    pass


class LocalLegacyProject(BaseProject):
    @property
    def metadata(self):
        # TODO: Call egg_info (req.req_install.InstallRequirement.run_egg_info)
        return


class LocalModernProject(BaseProject):
    @property
    def metadata(self):
        # TODO: if prepare_metadata_for_build_wheel is not implemented,
        #  raise NotImplementedError.
        # TODO: call prepare_metadata_for_build_wheel (
        #  req.req_install.InstallRequirement.prepare_pep517_metadata)
        # TODO: cache result
        return

    def __next__(self):
        # TODO: Build project into wheel
        #
        return LocalWheel(self)

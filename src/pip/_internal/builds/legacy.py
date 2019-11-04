from pip._internal.utils.typing import MYPY_CHECK_RUNNING

if MYPY_CHECK_RUNNING:
    from typing import List


class LegacyBuildHelper(object):
    def __init__(
        self,
        location,  # type: str
        global_options,  # type: List[str]
        isolated,  # type: bool
        install_options,  # type: List[str]
    ):
        ...

    def install(self, scheme):
        ...


def legacy_build_wheel(
    name,  # type: str
    source_dir,
    build_env,
    global_options,
    setup_py_path,
    build_options,
    unpacked_source_directory,
):
    # Given data, try to build a wheel.
    pass

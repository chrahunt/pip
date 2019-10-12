"""Configuration represents inputs that alter the behavior of project
preparation.
"""

from pip._internal.commands.install import is_wheel_installed


class ProjectConfig(object):
    """Configuration propagated between projects.
    """
    def __init__(
        self,
        isolated,  # type: bool
        use_pep517,  # type: bool
        legacy_wheel_build=is_wheel_installed(),
    ):
        self.isolated = isolated
        self.use_pep517 = use_pep517
        self.legacy_wheel_build = legacy_wheel_build

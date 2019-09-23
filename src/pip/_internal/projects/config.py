"""Configuration represents inputs that alter the behavior of project
preparation.
"""

class ProjectConfig(object):
    """Configuration propagated between projects.
    """
    def __init__(
        self,
        isolated,  # type: bool
        use_pep517,  # type: bool
    ):
        self.isolated = isolated
        self.use_pep517 = use_pep517

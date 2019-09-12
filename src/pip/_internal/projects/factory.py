from pip._internal.projects.projects import BaseProjectWithInit


class ProjectFactory(object):
    """
    Does some of the work of
    - local_resolve.Resolver
    - operations.prepare.Preparer

    to initialize a project based on something which may represent:
    1. remote link
    2. local directory
    3. installed distribution

    There's some overlap between this and the Candidates returned by
    PackageFinder, need to identify what that is.
    """
    def __init__(self):
        pass

    def from_requirement(self, req):
        """
        Given a requirement, construct a project for it.
        """
        pass

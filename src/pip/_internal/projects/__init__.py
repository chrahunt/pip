"""Projects package.

Projects represent the states that a known Python package can be in, for
example:

1. A link to a VCS repository that (if installed) should be editable
2. An local directory holding a legacy project that has been built into a wheel
3. A local path to a source distribution archive

and more.


"""
# Explicitly import projects so they are registered.
import pip._internal.projects.projects  # noqa

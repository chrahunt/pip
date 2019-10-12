import logging
from collections import namedtuple
from textwrap import dedent

import pytest
from mock import Mock

from pip._internal.locations import distutils_scheme
from pip._internal.models.requirement import parse_requirement
from pip._internal.projects.factory import ProjectFactory
from pip._internal.projects.project import Project
from pip._internal.projects.projects import (
    LocalLegacyProject,
    LocalLegacyNonWheelProject,
    LocalNonEditableDirectory,
    LocalWheel,
    ProjectContext,
    UnpackedSources,
    UnpackedWheel,
)
from tests.lib import create_test_package_with_setup
from tests.lib.path import Path


logger = logging.getLogger(__name__)


class ProjectInfo(object):
    def __init__(self, path):
        self._path = path

    @property
    def path(self):
        return str(self._path)

    def as_req(self, **kwargs):
        return parse_requirement(self.path, **kwargs)


@pytest.fixture
def legacy_project_factory(tmpdir_factory):
    def factory(**setup_kwargs):
        tmpdir = Path(tmpdir_factory.mktemp(setup_kwargs['name']))
        script = Mock(scratch_path=tmpdir)
        # TODO: Make create_test_* helpers more generic.
        return ProjectInfo(create_test_package_with_setup(script, **setup_kwargs))

    return factory


def assert_matching_states(project, states):
    # type: (Project, List[type(BaseProject)])
    project_states = [project._project]
    try:
        while True:
            project._prepare()
            project_states.append(project._project)
    except NotImplementedError:
        pass

    state_types = [
        type(s) for s in project_states
    ]
    assert state_types == states, project


def test_local_legacy_non_editable_directory_install(legacy_project_factory, example_scheme):
    """Example of checking the full sequence of states transitioned
    through for a project.
    """
    project_info = legacy_project_factory(name='example')
    req = project_info.as_req(source='test', editable=False, constraint=False)
    factory = ProjectFactory(Mock(use_pep517=None), Mock())
    project = factory.from_requirement(req)

    assert_matching_states(
        project,
        [
            LocalNonEditableDirectory,
            UnpackedSources,
            LocalLegacyProject,
            LocalWheel,
            UnpackedWheel,
        ],
    )


def test_unpacked_sources_transition_legacy(legacy_project_factory):
    """Example checking a single state transition.
    """
    project_info = legacy_project_factory(name='example')
    ctx = ProjectContext(Mock(use_pep517=None), Mock())
    project = UnpackedSources(ctx, project_info.path, 'test')

    new_project = project.prepare()

    assert isinstance(new_project, LocalLegacyProject)


def test_legacy_metadata(legacy_project_factory):
    project_info = legacy_project_factory(
        name='example', version='0.1.0'
    )

    ctx = ProjectContext(Mock(), Mock())
    project = LocalLegacyProject(ctx, project_info.path)
    assert project.name == 'example'
    assert project.version == '0.1.0'


def test_legacy_wheel_build(legacy_project_factory):
    project_info = legacy_project_factory(
        name='example', version='0.1.0'
    )

    ctx = ProjectContext(Mock(), Mock())
    project = LocalLegacyProject(ctx, project_info.path)
    new_project = project.prepare()
    assert isinstance(new_project, LocalWheel), new_project


def test_legacy_non_wheel_prepare(legacy_project_factory):
    project_info = legacy_project_factory(
        name='example', version='0.1.0'
    )

    # Explicitly disable legacy wheel building (like wheel not being
    # installed)
    ctx = ProjectContext(Mock(legacy_wheel_build=False), Mock())
    project = LocalLegacyProject(ctx, project_info.path)
    new_project = project.prepare()
    assert isinstance(new_project, LocalLegacyNonWheelProject), new_project


@pytest.fixture
def example_scheme(tmpdir):
    base_install = tmpdir / 'env'
    lib_dir = base_install / 'lib'
    lib_dir.mkdir(parents=True)
    bin_dir = base_install / 'bin'
    bin_dir.mkdir(parents=True)
    header_dir = base_install / 'include'
    header_dir.mkdir(parents=True)
    data_dir = base_install
    data_dir.mkdir(parents=True, exist_ok=True)

    scheme = {
        'purelib': str(lib_dir),
        'platlib': str(lib_dir),
        'scripts': str(bin_dir),
        'data': str(data_dir),
        'headers': str(header_dir),
    }

    return scheme


def test_legacy_wheel_install(legacy_project_factory, example_scheme, tmpdir):
    # End-to-end test of a wheel install.
    project_info = legacy_project_factory(
        name='example', version='0.1.0'
    )

    ctx = ProjectContext(Mock(), Mock())
    project = Project(LocalLegacyProject(ctx, project_info.path))
    try:
        project.install(example_scheme)
    except Exception:
        logger.info("Failed for %r", project)
        raise


    dist_info_dir = Path(example_scheme['purelib']) / 'example-0.1.0.dist-info'
    assert dist_info_dir.exists()

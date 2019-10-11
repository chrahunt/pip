from textwrap import dedent

import pytest
from mock import Mock

from pip._internal.models.requirement import parse_requirement
from pip._internal.projects.factory import ProjectFactory
from pip._internal.projects.projects import (
    LocalLegacyProject,
    LocalNonEditableDirectory,
    ProjectContext,
    UnpackedSources,
)
from tests.lib import create_test_package_with_setup
from tests.lib.path import Path


@pytest.fixture
def legacy_project_factory(tmpdir_factory):
    def factory(**setup_kwargs):
        tmpdir = Path(tmpdir_factory.mktemp(setup_kwargs['name']))
        script = Mock(scratch_path=tmpdir)
        return create_test_package_with_setup(script, **setup_kwargs)
    return factory


def test_local_non_editable_directory_transition(legacy_project_factory):
    project_dir = legacy_project_factory(name='example')

    req = parse_requirement(
        str(project_dir), source='test', editable=False, constraint=False
    )
    ctx = ProjectContext(Mock(), Mock())
    project = LocalNonEditableDirectory.from_req(ctx, req)

    new_project = project.prepare()

    assert isinstance(new_project, UnpackedSources)


def test_unpacked_sources_transition_legacy(legacy_project_factory):
    project_dir = legacy_project_factory(name='example')

    ctx = ProjectContext(Mock(use_pep517=None), Mock())
    project = UnpackedSources(ctx, str(project_dir), 'test')

    new_project = project.prepare()

    assert isinstance(new_project, LocalLegacyProject)


def test_legacy_metadata(legacy_project_factory):
    project_dir = legacy_project_factory(
        name='example', version='0.1.0'
    )

    ctx = ProjectContext(Mock(), Mock())
    project = LocalLegacyProject(ctx, str(project_dir))
    assert project.name == 'example'
    assert project.version == '0.1.0'

import pytest
from mock import Mock

from pip._internal.models.requirement import parse_requirement
from pip._internal.projects.factory import ProjectFactory
from pip._internal.projects.projects import LocalNonEditableDirectory


def create_parsed_requirement(src):
    return parse_requirement(
        src['src'],
        source='<test>',
        editable=src.get('editable', False),
        constraint=False,
    )


@pytest.fixture(scope='module')
def factory():
    # type: () -> ProjectFactory
    config = Mock()
    services = Mock()
    yield ProjectFactory(config, services)


@pytest.mark.parametrize("src,cls", [
    (dict(src='.'), LocalNonEditableDirectory),
])
def test_expected_project_created(src, cls, factory):
    parsed_requirement = create_parsed_requirement(src)
    instance = factory.from_requirement(parsed_requirement)
    assert isinstance(instance, cls)

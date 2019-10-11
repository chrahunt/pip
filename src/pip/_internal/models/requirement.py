from pip._internal.req.constructors import (
    parse_req_from_editable,
    parse_req_from_line,
)
from pip._internal.utils.typing import MYPY_CHECK_RUNNING

if MYPY_CHECK_RUNNING:
    from typing import List, Optional

    from pip._internal.req.constructors import RequirementParts


class ParsedRequirement(object):
    """Represents an input requirement.
    """
    def __init__(
        self,
        parts,  # type: RequirementParts
        editable,  # type: bool
        constraint,  # type: bool
        build_options,  # type: List[str]
        install_options,  # type: List[str]
        global_options,  # type: List[str]
    ):
        self.parts = parts
        self.editable = editable
        self.constraint = constraint
        self.build_options = build_options
        self.install_options = install_options
        self.global_options = global_options


def parse_requirement(
    req,  # type: str
    source,  # type: str
    editable,  # type: bool
    constraint,  # type: bool
    build_options=None,  # type: Optional[List[str]]
    install_options=None,  # type: Optional[List[str]]
    global_options=None,  # type: Optional[List[str]]
):
    # type: (...) -> ParsedRequirement
    """
    :param req: the input requirement string
    :param source: the source of the requirement, for logging
    :param editable: whether the requirement is editable
    :param constraint: whether the requirement is a constraint
    :param build_options: TBD
    :param install_options: TBD
    :param global_options: TBD
    :return: the generated ParsedRequirement
    """
    if editable:
        parts = parse_req_from_editable(req)
    else:
        parts = parse_req_from_line(req, source)

    return ParsedRequirement(
        parts,
        editable,
        constraint,
        build_options or [],
        install_options or [],
        global_options or [],
    )

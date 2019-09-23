from pip._internal.utils.typing import MYPY_CHECK_RUNNING

if MYPY_CHECK_RUNNING:
    from pip._internal.models.link import Link


class DownloadService(object):
    def __call__(self, link, output_path):
        # type: (Link, str) -> None
        raise NotImplementedError('TODO')


class ProjectServices(object):
    def __init__(self):
        self.download = DownloadService()

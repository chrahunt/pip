from pip._internal.models.link import Link


class DownloadService(object):
    def __call__(self, link, output_path):
        # type: (Link, str) -> None
        ...


class ProjectServices(object):
    def __init__(self):
        self.download = DownloadService()

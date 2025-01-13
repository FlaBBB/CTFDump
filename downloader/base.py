import logging


class BaseSource:
    def __init__(self, manager, session):
        self.manager = manager
        self.session = session
        self.logger = logging.getLogger(self.__class__.__name__)

    def download(self, url: str, path: str) -> None:
        raise NotImplementedError

    def is_valid(self, url: str) -> bool:
        raise NotImplementedError

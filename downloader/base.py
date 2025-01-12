class BaseSource:
    def __init__(self, manager, session):
        self.manager = manager
        self.session = session

    def download(self, url: str) -> None:
        raise NotImplementedError

    def is_valid(self, url: str) -> bool:
        raise NotImplementedError

from abc import ABC, abstractmethod


class Command(ABC):
    @abstractmethod
    def set_args(self, the_args):
        pass

    @abstractmethod
    def run_command(self):
        pass

    @abstractmethod
    def parse_args(self):
        pass


class Parameter:
    def __init__(self, key=None, value=None):
        self.key = key
        self.value = value


class ParameterList:
    def __init__(self, params=None):
        if params is None:
            params = {}
        self.params = params



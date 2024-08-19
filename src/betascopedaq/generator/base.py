import abc


class Generator(abc.ABC):
    """
    Abstract class for waveform generator.
    """

    @abc.abstractmethod
    def connect(self, *args, **kwargs):
        """
        This method initiate the connection to the scope.
        """

    @abc.abstractmethod
    def initialize(self, *args, **kwargs):
        """
        This method initiate the scope setup.
        """

    @abc.abstractmethod
    def reset(self, *args, **kwarg):
        """
        This method use for resetting scope.
        """

    @abc.abstractmethod
    def close(self, *args, **kwarg):
        """
        This method use for closing scope and cleanup.
        """

    @abc.abstractmethod
    def write(self, *args, **kwarg):
        """
        This method use for sending command.
        """

    @abc.abstractmethod
    def query(self, *args, **kwarg):
        """
        This method use for sending command.
        """

    @abc.abstractmethod
    def read(self, *args, **kwarg):
        """
        This method use for sending command.
        """

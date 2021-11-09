#!/usr/bin/env python3

import abc


class Scope(abc.ABC):
    """
    Abstract class for scopes.
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
    def get_waveform(self, *args, **kwargs):
        """
        This method should return waveform from the scope
        """

    @abc.abstractmethod
    def set_trigger(self, *args, **kwargs):
        """
        This method should set triggering.
        """

    @abc.abstractmethod
    def wait_trigger(self, *args, **kwargs):
        """
        This method should wait for event triggering.
        """

    @abc.abstractmethod
    def enable_channel(self, *args, **kwarg):
        """
        This method should use for enable/disable scope channel.
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

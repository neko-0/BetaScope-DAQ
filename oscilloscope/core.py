#!/usr/bin/env python3


import abc


class Scope(abc.ABC):
    """
    Abstract class for scopes.
    """

    @abc.abstractclassmethod
    def MakeScope(cls, ip_address):
        """
        This class method should return a scope instance.
        """

    @abc.abstractmethod
    def InitSetup(self, *argv):
        """
        This method initiate the scope setup.
        """

    @abc.abstractmethod
    def GetWaveform(self, channel_list, mode, seq_mode, *argv):
        """
        This method should return waveform from the scope
        """

    @abc.abstractmethod
    def WaitTrigger(self, timeout, *argv):
        """
        This method should wait for event triggering.
        """

    @abc.abstractmethod
    def SetTrigger(self, channel, threshold, polarity, mode, *argv):
        """
        This method should set the scope trigger.
        """

    @abc.abstractmethod
    def Enable_Channel(self, channel, option):
        """
        This method should use for enable/disable scope channel.
        """

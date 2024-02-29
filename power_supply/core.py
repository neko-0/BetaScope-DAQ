#!/usr/bin/env python3


import abc


class PowerSupply(abc.ABC):
    """
    Abstract class for powser supply.
    """

    @abc.abstractclassmethod
    def MakePS(cls, ip_address):
        """
        This class method should return a power supply instance.
        """

    @abc.abstractmethod
    def InitSetup(self, *argv):
        """
        This method initiate with setup.
        """

    @abc.abstractmethod
    def Enable_Channel(self, channel, option, *argv):
        """
        This mehtod should enable/diable channel
        """

    @abc.abstractmethod
    def SetVoltage(self, channel, volt, maxI, *argv):
        """
        This method should set the voltage in ps.
        """

    @abc.abstractmethod
    def ConfirmVoltage(self, channel, volt, *argv):
        """
        This method should confirm the voltage in ps.
        """

    @abc.abstractmethod
    def CurrentReader(self, channel, *argv):
        """
        This method should read the current from ps channel.
        """

    @abc.abstractmethod
    def VoltageReader(self, channel, *argv):
        """
        This method should read the voltage from ps channel.
        """

    @abc.abstractmethod
    def Close(self):
        """
        This method should close the ps.
        """

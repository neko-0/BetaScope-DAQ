#!/usr/bin/env python3


import abc

class Scope(abc.ABC):
    """
    Abstract class for scopes.
    """

    @abc.abstractmethod
    def GetWaveform(self):
        """
        This method should return waveform from the scope
        """

    @abc.abstractmethod
    def WaitTrigger(self):
        """
        This method should wait for event triggering.
        """

    @abc.abstractmethod
    def SetTrigger(self):
        """
        This method should set the scope trigger.
        """

    

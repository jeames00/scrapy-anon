from __future__ import annotations
from abc import ABC, abstractmethod

class Subject(ABC):

    @abstractmethod
    def attach(self, observer: Observer) -> None:
        """
        Attach an observer to receive notifications
        """
        pass

    @abstractmethod
    def detach(self, observer: Observer) -> None:
        """
        Detach an observer
        """
        pass

    @abstractmethod
    def notify(self) -> None:
        """
        Notify all observers of a change
        """
        pass

class Observer(ABC):

    @abstractmethod
    def update(self, subject: Subject) -> None:
        """
        Do something when notified of a change
        """
        pass

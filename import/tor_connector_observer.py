import logging

from scrapyanon.ObserveNotify import Subject, Observer

class TorConnectorObserver(Observer):

    def __init__(self):
        self.custom_circuit_status = None

    def update(self, subject: Subject) -> None:
        self.custom_circuit_status = subject.custom_circuit_status
        logging.debug("TorConnectorObserver detected custom circuit '{}' status change to: {}".format(
            subject.custom_circuit, subject.custom_circuit_status))

    @property
    def custom_circuit_status(self):
        return self._custom_circuit_status

    @custom_circuit_status.setter
    def custom_circuit_status(self, value):
        self._custom_circuit_status = value

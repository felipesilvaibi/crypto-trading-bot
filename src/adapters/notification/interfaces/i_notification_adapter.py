from abc import ABC, abstractmethod


class INotificationAdapter(ABC):
    @abstractmethod
    def send_message(self, message: str) -> None:
        """
        Sends a message to a specified destination.

        :param message: The content of the message to be sent.
        :type message: str
        """
        pass

import base64
import hashlib


class User:

    def __init__(self) -> None:
        """Initialize the user object."""
        self.__username: str = ""
        self.__pw_hash: str = ""
        self.__do_registration: bool = False
        self.__start_authentication: bool = False
        self.__authed: bool = False
        self.__encr_key: bytes = b""
        self.__rx_message_buffer: list = []
        self.__tx_message_buffer: list = []

    def set_username(self, username: str) -> None:
        """Set the username."""
        self.__username = username

    def get_username(self) -> str:
        """Get the username."""
        return self.__username

    def set_pw_hash(self, password: str) -> None:
        """Set the password hash."""
        passwd_hash = hashlib.sha3_512(password.encode("utf-8")).hexdigest()
        self.__pw_hash = passwd_hash

    def get_pw_hash(self) -> str:
        """Get the password hash."""
        return self.__pw_hash

    def set_do_registration(self, operation: bool) -> None:
        """Set whether the user has requested to register."""
        self.__do_registration = operation

    def get_do_registration(self) -> bool:
        """Get whether the user has requested to register"""
        return self.__do_registration

    def set_start_authentication(self, status: bool) -> None:
        """Set whether the user is authenticating."""
        self.__start_authentication = status

    def get_start_authentication(self) -> bool:
        """Get whether the user is authenticating."""
        return self.__start_authentication

    def set_authed(self, status: bool) -> None:
        """Set whether the user has been authenticated."""
        self.__authed = status

    def get_authed(self) -> bool:
        """Get whether the user is authenticated."""
        return self.__authed

    def set_encr_key(self, key: str) -> None:
        """Set the encryption key with user supplied password."""
        encoded_key = base64.b64encode(f"{key:<32}".encode("utf-8"))
        self.__encr_key = encoded_key

    def get_encr_key(self) -> bytes:
        """Get the encryption key."""
        return self.__encr_key

    def add_to_rx_message_buffer(self, message: str) -> None:
        """Add the message to the receive buffer."""
        self.__rx_message_buffer.append(message)

    def clear_rx_message_buffer(self) -> None:
        """Clear the receive buffer."""
        self.__rx_message_buffer = []

    def get_rx_message_buffer(self) -> list:
        """Get the receive buffer."""
        return self.__rx_message_buffer

    def add_to_tx_message_buffer(self, message: str) -> None:
        """Add the message to the transmit buffer."""
        self.__tx_message_buffer.append(message)

    def clear_tx_message_buffer(self) -> None:
        """Clear the transmit buffer."""
        self.__tx_message_buffer = []

    def get_tx_message_buffer(self) -> list:
        """Get the transmit buffer."""
        return self.__tx_message_buffer

import json
import socket
import threading
import time

from cryptography.fernet import Fernet, InvalidToken

from tui.chat_ui import ChatTUI
from tui.login_form import LoginTUI
from user import User


class Client:
    def __init__(self, user_obj: User) -> None:
        # user supplied user object from parameter
        self.__user = user_obj

        # create a new socket object that uses IPv4 and TCP
        self.__client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    @staticmethod
    def __encrypt_message(message: str, key: bytes) -> bytes:
        """
        Encrypts a string using Fernet with supplied key.

        :param message: message string to encrypt
        :param key: encryption key
        :return: encrypted messages
        """
        cipher = Fernet(key)
        encrypted_message = cipher.encrypt(message.encode())
        return encrypted_message

    @staticmethod
    def __decrypt_message(encrypted_message: bytes, key: bytes) -> str or None:
        """
        Decrypts a message in bytes using Fernet with supplied key

        :param encrypted_message: message in bytes to decrypt
        :param key: decryption key
        :return: decrypted message or None if message couldn't be decrypted
        """
        # try to decrypt message using Fernet and provided key
        try:
            cipher = Fernet(key)
            decrypted_message = cipher.decrypt(encrypted_message).decode()
        # if it fails, set decrypted_message to None
        except InvalidToken:
            decrypted_message = None
        # return the decrypted message or None according to decryption attempt success
        return decrypted_message

    def __send_message(self) -> None:
        """
        Polls the tx message buffer for new messages and sends them using the client socket.
        """
        # use user object and client socket object
        user = self.__user
        sock = self.__client

        # get encryption key from the user object
        encr_key = self.__user.get_encr_key()

        # as long as the thread runs, send user input messages
        while True:
            # check every 100ms to avoid using too many cpu cycles
            time.sleep(0.1)

            # get message buffer list from user object
            message_buffer = user.get_tx_message_buffer()

            # if message buffer is empty, skip sending procedure
            if not message_buffer:
                continue

            # send every message in the buffer
            for msg in message_buffer:
                # encrypt the message using the __encrypt_message method
                encrypted_msg = self.__encrypt_message(msg, encr_key)

                # send the encrypted message to the server
                sock.send(encrypted_msg)

                # iterate every 100ms to avoid losing messages when transmitting (too fast)
                time.sleep(0.1)

            # clear the message buffer after every message has been sent
            user.clear_tx_message_buffer()

    def __receive_message(self) -> None:
        """
        Receives messages using the client socket, decrypts them and appends them to the rx message buffer.
        """
        # use the clients socket
        sock = self.__client

        # get encryption key from user object
        decr_key = self.__user.get_encr_key()

        # as long as the thread runs, receive messages
        while True:
            # receive user data as json and convert to dict
            received_data_json = sock.recv(1024).decode("utf-8")
            received_data = json.loads(received_data_json)

            # decrypt message using __decrypt_message method
            decrypted_message = self.__decrypt_message(received_data["message"].encode(), decr_key)

            # if message could be decrypted, add it to the rx message buffer
            if decrypted_message is not None:
                self.__user.add_to_rx_message_buffer(message=f"{received_data['username']}: {decrypted_message}")

    @staticmethod
    def __do_login(sock: socket.socket, username: str, pw_hash: str) -> str:
        """
        Login to the server using the client's socket and provided credentials from the user object.

        :param sock: The client's socket
        :param username: The username of the user requesting the log-in
        :param pw_hash: The pw_hash of the user requesting the log-in
        :return: A string indicating the success of the login operation ("OK"/"NOT OK")
        """
        # set the operation to send to the server as "login"
        operation = "login"

        # put user credentials into a dict and convert to json
        user_data = {"operation": operation, "username": username, "pw_hash": pw_hash}
        user_data_json = json.dumps(user_data)

        # send user data and requested operation to the server
        sock.send(user_data_json.encode("utf-8"))

        # receive the server's feedback to sent credentials
        server_feedback = sock.recv(1024).decode("utf-8")

        return server_feedback

    @staticmethod
    def __do_registration(sock: socket.socket, username: str, pw_hash: str) -> str:
        """
        Register to the server using the client's socket and provided credentials from the user object.

        :param sock: The client's socket
        :param username: The username of the user requesting the registration
        :param pw_hash: The pw_hash of the user requesting the registration
        :return: A string indicating the success of the login operation ("OK"/"NOT OK")
        """
        # set the operation to send to the server as "register"
        operation = "register"

        # put user credentials into a dict and convert to json
        user_data = {"operation": operation, "username": username, "pw_hash": pw_hash}
        user_data_json = json.dumps(user_data)

        # send user data and requested operation to the server
        sock.send(user_data_json.encode("utf-8"))

        # receive the server's feedback to sent credentials
        server_feedback = sock.recv(1024).decode("utf-8")

        return server_feedback

    def __authenticate_user(self) -> str:
        """
        Authenticate the user using the client's socket with the provided credentials from the user object

        :return: A string indicating the success of the authentication attempt ("OK"/"NOT OK")
        """
        # get user supplied username and password (hash) from the user object
        username = self.__user.get_username()
        passwd_hash = self.__user.get_pw_hash()

        # if user has requested to register, start the registration procedure
        if self.__user.get_do_registration():
            server_feedback = self.__do_registration(self.__client, username, passwd_hash)
        # if not, start the login procedure
        else:
            server_feedback = self.__do_login(self.__client, username, passwd_hash)

        return server_feedback

    def __handle_authentication(self) -> None:
        """
        Initializes the user authentication and communicates with the GUI via polling the user object.
        """
        user = self.__user

        # while user has not been authed, try to auth the user
        while not user.get_authed():
            # as long as the user has not requested to log-in (via the LoginTUI), wait
            while not user.get_start_authentication():
                time.sleep(0.1)

            # get server feedback from the authentication method
            server_feedback = self.__authenticate_user()

            # set auth status of the user object according to the server feedback
            if server_feedback == "OK":
                user.set_authed(True)
            else:
                user.set_authed(False)

            # mark authentication attempt as done
            user.set_start_authentication(False)

    def __init_messaging(self) -> None:
        """
        Sets up the messaging (sending and receiving) threads and ChatTUI and starts them.
        """
        # initialize the messaging for receiving and sending messages
        send_thread = threading.Thread(target=self.__send_message)
        recv_thread = threading.Thread(target=self.__receive_message)

        # send threads as daemon, so they terminate if the program does
        send_thread.daemon = True
        recv_thread.daemon = True

        # start the messaging threads
        send_thread.start()
        recv_thread.start()

        # create chat_ui object from ChatTUI and run the chat UI
        chat_ui = ChatTUI(user=self.__user)
        chat_ui.run()

    def __init_authentication(self) -> None:
        """
        Sets up the authentication thread and ChatTUI and starts them.
        """
        # initialize and start the client class' authentication method as thread
        auth_thread = threading.Thread(target=self.__handle_authentication)
        auth_thread.daemon = True
        auth_thread.start()

        # create object for LoginTUI and run LoginTUI
        login_form = LoginTUI(self.__user)

        # run login form, exit program if return code is 1 (keyboard interruption)
        return_code = login_form.run()
        if return_code == 1:
            exit(1)

        # join the auth thread after authentication succeeded
        auth_thread.join()

    def __connect(self, server_ip: str, server_port: int) -> None:
        """
        Connect to the server using the client's socket.

        :param server_ip: IP address of the target server
        :param server_port: Port of the target server
        """
        connected = False

        # try to connect as long as connection attempts have not been successful
        while not connected:
            try:
                self.__client.connect((server_ip, server_port))
                connected = True
            except ConnectionRefusedError:
                print("Connection refused, retrying...")
                time.sleep(5)

    def start(self, server_ip: str, server_port: int) -> None:
        """
        Starts the methods for connecting to the server, initializing authentication and initializing messaging.

        :param server_ip: IP address of the target server
        :param server_port: Port of the target server
        """
        # connect to server
        self.__connect(server_ip, server_port)

        # initialize and start authentication thread and login form UI
        self.__init_authentication()

        # initialize and start messaging threads and chat UI
        self.__init_messaging()

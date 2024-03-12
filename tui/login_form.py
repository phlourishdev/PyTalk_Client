import time

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Tabs, Tab, Label, Input, Button


class LoginTUI(App):

    BINDINGS = [("ctrl+c", "exit", "Exit the program")]
    CSS_PATH = "login_form.tcss"

    def __init__(self, user) -> None:
        # copy everything from the superclass' constructor
        App.__init__(self)

        # utilize user parameter value as user object
        self.__user = user

    def compose(self) -> ComposeResult:
        """
        Textual method which yields the widgets.
        """
        yield Header()
        yield Tabs(
            Tab(label="login", id="login-tab"),
            Tab(label="register", id="register-tab"),
        )
        yield Label()
        yield Input(
            placeholder="Username",
            id="username-input",
            max_length=12
        )
        yield Input(
            placeholder="Password",
            id="password-input",
            max_length=128,
            password=True
        )
        yield Input(
            placeholder="Encryption Key",
            id="encr-key-input",
            max_length=128,
            password=True
        )
        yield Button(label="Submit")
        yield Footer()

    def on_ready(self) -> None:
        """
        Textual method which gets executed after UI has been loaded.
        """
        # set the window title
        self.title = "PyTalk"

        # put focus on the first input field
        self.query_one(selector="#username-input").focus()

    def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        """
        Textual method which gets executed, as soon as tab has been changed. Changes the subtitle.
        :param event: Tab activated event
        """
        # change window subtitle according to selected tab label
        self.sub_title = event.tab.label

    def __check_user_credentials(self, operation: str) -> None:
        """
        Uses polling to communicate user credentials with the server class.
        :param operation: Set to "register" or "login"
        """
        # set the user's registration attribute according to operation parameter value
        self.__user.set_do_registration(operation == "register")

        # set start_authentication to True, indicating the client class to start the auth process
        self.__user.set_start_authentication(True)

        # as long as the client class hasn't changed the start_authentication attribute, wait
        while self.__user.get_start_authentication():
            # wait 100ms to avoid using up to many cpu cycles
            time.sleep(0.1)

        # if user has got successfully authenticated, exit the UI
        if self.__user.get_authed():
            self.exit()
        # if not, show the respective error message
        else:
            if operation == "login":
                feedback_message = "Wrong credentials. Try again."
            else:
                feedback_message = "Account already exists."
            self.query_one(Label).update(feedback_message)

    def __submit_user_credentials(self) -> None:
        """
        Submits user credentials that have been entered by the user and writes them to the user object.
        Initializes the authentication process communication with the client class.
        """
        # get credentials from input fields
        user = self.query_one(selector="#username-input", expect_type=Input).value
        pw = self.query_one(selector="#password-input", expect_type=Input).value
        encr_key = self.query_one(selector="#encr-key-input", expect_type=Input).value

        # if one of them is empty, return
        if not (user and pw and encr_key):
            return

        # set user object attributes according to user input
        self.__user.set_username(username=user)
        self.__user.set_pw_hash(password=pw)
        self.__user.set_encr_key(key=encr_key)

        # get the currently selected tab title, which is used to determine if the user chose to log in or to register
        selected_tab = self.sub_title

        # initiate user credential check
        self.__check_user_credentials(operation=selected_tab)

    def on_input_submitted(self) -> None:
        """
        Textual method which gets executed when input from an input field is submitted by the user.
        """
        self.__submit_user_credentials()

    def on_button_pressed(self) -> None:
        """
        Textual method which gets executed when the button is pressed by the user.
        """
        self.__submit_user_credentials()

    def action_exit(self):
        """
        Executed when the user presses ctrl+c to exit the program.
        :return: 1 to indicate keyboard interruption
        """
        self.exit(1)

import asyncio

from textual.app import App, ComposeResult
from textual.widgets import Log, Input, Footer


class ChatTUI(App):
    # subclass of App from Textual

    BINDINGS = [("ctrl+x", "clear_log", "Clear message history")]

    def __init__(self, user):
        # copy everything of the superclass' constructor
        App.__init__(self)

        # utilize user parameter value as user object
        self.__user = user

    def compose(self) -> ComposeResult:
        """
        Textual method which yields the widgets.
        """
        yield Log(auto_scroll=True, id="chat-out")
        yield Input(placeholder="Enter some text...", max_length=100)
        yield Footer()

    def on_ready(self) -> None:
        """
        Textual method which gets executed after UI has been loaded.
        """
        # put focus on the input widget
        self.query_one(Input).focus()

        # create task to update the log in the background
        asyncio.create_task(self.__update_log())

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """
        Textual method which gets executed when input from an input field is submitted by the user.
        """
        # write input contents to the log
        self.query_one(Log).write_line("you: " + event.value)

        # add input contents to the transmit message buffer
        self.__user.add_to_tx_message_buffer(message=event.value)

        # clear the input field
        self.query_one(Input).clear()

    def action_clear_log(self) -> None:
        """
        Textual method which gets executed on ctrl+x, see BINDINGS. Clears the message history.
        """
        self.query_one(Log).clear()

    async def __update_log(self) -> None:
        """
        Checks rx message buffer for new messages and updates the log accordingly.
        """
        # get log widget as log_output
        log_output = self.query_one(selector="#chat-out")

        # as long as the task is running
        while True:
            # get the received messages buffer
            message_buffer = self.__user.get_rx_message_buffer()

            # as long as the message buffer is empty, wait
            while not message_buffer:
                message_buffer = self.__user.get_rx_message_buffer()
                # wait 100ms to avoid using up to many cpu cycles
                await asyncio.sleep(0.1)

            # write contents of message buffer to the log
            for message in message_buffer:
                log_output.write_line(message)

            # clear the message buffer
            self.__user.clear_rx_message_buffer()

            # wait 100ms to avoid using up to many cpu cycles
            await asyncio.sleep(0.1)

from client import Client
from user import User

HOST: str = "localhost"
PORT: int = 55555


if __name__ == "__main__":
    user = User()
    client = Client(user_obj=user)
    client.start(server_ip=HOST, server_port=PORT)

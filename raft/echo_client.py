import contextlib
import socket
import attrs

from raft.utils import start_client, create_logger, StructLogger, SocketStream


@attrs.define()
class EchoClient:
    host: str = "localhost"
    port: int = 10000

    sock: socket.socket = attrs.field(init=False)
    sock_stream: SocketStream = attrs.field(init=False)
    logger: StructLogger = attrs.field(init=False, factory=create_logger)

    def __attrs_post_init__(self) -> None:
        self.sock = start_client(self.host, self.port)
        self.sock_stream = SocketStream(self.sock)
        self.logger.info("Started client", host=self.host, port=self.port)

    def try_send(self, command: str, key: str | None, value: str | None):
        msg = f"{command} {key or ''} {value or ''}"
        self.logger.info("Client sending message", message=msg)
        with contextlib.suppress(Exception):
            self.send_and_recv(msg)

    def send_and_recv(self, msg: str) -> str:
        # Send data
        self.sock_stream.send(msg)
        # Look for the response
        msg = self.sock_stream.recv()
        self.logger.info("Client received message", message=msg)
        return msg

    def __del__(self):
        self.logger.info("Client closing socket")
        if hasattr(self, "sock"):
            self.sock.close()

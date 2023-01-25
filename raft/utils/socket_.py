import socket
import typing as t

import attrs
from tqdm.rich import tqdm

from raft.utils.logging_ import create_logger, StructLogger


class ConnectedServer(t.NamedTuple):
    connection: socket.socket
    client_address: t.Tuple[str, int]


def start_server(host: str, port: int) -> socket.socket:
    """Start a server listening on the given host and port."""
    sock = socket.socket(
        # AF_INET is the Internet address family for IPv4.
        socket.AF_INET,
        # SOCK_STREAM is the socket type for TCP, the protocol that will be used to
        # transport our messages in the network.
        # TCP ensures that all data sent is received in the same order by the
        # receiving end.
        # TCP also ensures that all data is received and that none of the data is
        # lost along the way.
        socket.SOCK_STREAM,
    )
    # Arguments to bind depend on the address family of the socket.
    # In this case (AF_INET), it is expecting a tuple of host and port.
    sock.bind(
        (
            # Host is the hostname or IP address of the server. It can be an empty
            # string. If an empty string is passed, the server will listen on all
            # available IPv4 interfaces.
            # When using a hostname, you could see different results depending on the
            # value returned from the name resolution process.
            host,
            # Port represents the TCP port number to accept connections on from clients
            # It should be an integer between 0 and 65535. If port is 0, the OS will
            # assign an available port to the server.
            # Some systems will not allow you to use a port number less than 1024
            # unless you are running the server as a superuser.
            port,
        )
    )
    # Enables a server to accept connections. It makes it a “listening” socket.
    # Backlog is the maximum number of queued connections and should be at least 0;
    # the maximum value is system-dependent (usually 5), the minimum value is forced
    # to 0.
    # If not specified, a default reasonable value is chosen.
    # If the server receives a lot of connections, increasing the backlog value may
    # help it accept them faster when the operating system is ready to accept them.
    sock.listen()
    return sock


def start_client(host: str, port: int) -> socket.socket:
    """Start a client connecting to the given host and port."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    return sock


@attrs.define()
class SocketStream:
    """A socket that handles sending and receiving arbitrary length messages."""
    # May be client or server. Must have ready to receive and send messages
    sock: socket.socket

    logger: StructLogger = attrs.field(factory=create_logger)

    def recv(self) -> str:
        """Receive a message."""
        msg_len = self.recv_len()
        return self.recv_msg(msg_len)

    def recv_len(self) -> int:
        """Receive the length of the message."""
        self.logger.info("Receiving message length")
        msg_len = []
        while True:
            if not (msg_bytes := self.sock.recv(1)):
                raise RuntimeError("Socket connection broken")
            if msg_bytes.decode("utf-8") == "\0":
                break
            msg_len.append(msg_bytes.decode("utf-8"))
        return int("".join(msg_len))

    def recv_msg(self, msg_len: int) -> str:
        """Receive the message."""
        msg = []
        pbar = tqdm(total=msg_len, desc="Receiving message")
        while True:
            if not (msg_bytes := self.sock.recv(1)):
                raise RuntimeError("Socket connection broken")
            msg.append(msg_bytes.decode("utf-8"))
            pbar.update(1)
            if len(msg) == msg_len:
                break
        return "".join(msg)

    def send(self, msg: str) -> None:
        """Send the message."""
        msg_len = str(len(msg))
        self.sock.sendall(f"{msg_len}\0".encode("utf-8"))
        self.sock.sendall(msg.encode("utf-8"))

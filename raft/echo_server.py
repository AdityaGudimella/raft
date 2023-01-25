import socket
import time
import attrs

from raft.kv import KVStore
from raft.utils import start_server, create_logger, StructLogger, SocketStream


@attrs.define()
class EchoServer:
    host: str = "localhost"
    port: int = 10000
    kvs: KVStore = attrs.field(factory=KVStore)

    logger: StructLogger = attrs.field(factory=create_logger, init=False)
    sock: socket.socket = attrs.field(init=False)

    def __attrs_post_init__(self) -> None:
        self.sock = start_server(host=self.host, port=self.port)
        self.logger.info("Started server", host=self.host, port=self.port)

    def run(self) -> None:
        """Run the server."""
        while True:
            time.sleep(0.1)
            self.logger.info("Waiting for connection")
            # Block until a connection is made
            # When a client connects, a new socket object is returned
            # We need to use the new socket object to communicate with the client
            connection, client_address = self.sock.accept()
            self.logger.info(
                "Received connection from client", client_address=client_address
            )
            sock_stream = SocketStream(connection)
            try:
                msg = sock_stream.recv()
                response = self.kvs.execute(msg, persist=True)
                self.logger.info(
                    "Sending response back to client", response=response
                )
                sock_stream.send(response)
            finally:
                # Clean up the connection
                connection.close()

    def __del__(self) -> None:
        self.logger.info("Server closing socket")
        self.sock.close()


def run_server(host: str = "localhost", port: int = 10000) -> None:
    logger = create_logger()
    kvs = KVStore()

    sock = start_server(host=host, port=port)

    while True:
        logger.info("Waiting for connection")
        # Block until a connection is made
        # When a client connects, a new socket object is returned
        # We need to use the new socket object to communicate with the client
        connection, client_address = sock.accept()

        try:
            logger.info(
                "Received connection from client", client_address=client_address
            )

            # Receive the data in small chunks and retransmit it
            while True:
                if op_bytes := connection.recv(16):
                    response = kvs.execute(op_bytes, persist=True)
                    logger.info(
                        "Sending response back to the client", response=response
                    )
                    connection.sendall(response.encode("utf-8"))
                else:
                    logger.info("No data from client", client_address=client_address)
                    break
        finally:
            # Clean up the connection
            connection.close()


if __name__ == "__main__":
    EchoServer().run()

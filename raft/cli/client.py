import typer

from raft.echo_client import EchoClient


app = typer.Typer()


@app.command()
def send(
    command: str = typer.Argument(..., help="The command to send to the server"),
    key: str = typer.Option(
        None, "-k", "--key", help="The key to set or delete from server"
    ),
    value: str = typer.Option(
        None, "-v", "--value", help="The value to set on the server"
    ),
):
    """Start a new raft client"""
    EchoClient().try_send(command=command, key=key, value=value)

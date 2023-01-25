import typer

from raft.echo_server import EchoServer

app = typer.Typer()


@app.command()
def start():
    """Start a new raft server"""
    EchoServer().run()

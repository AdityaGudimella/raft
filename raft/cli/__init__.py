import typer

from raft.cli import client, server

app = typer.Typer()
app.add_typer(client.app, name="client")
app.add_typer(server.app, name="server")

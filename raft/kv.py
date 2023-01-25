import json
import typing as t
from pathlib import Path

import attrs
import pydantic as pdt

from raft.utils import create_logger, StructLogger


LOG_FILE = Path("/tmp/raft_commands.log")


class Operation(pdt.BaseModel):
    command: str = pdt.Field()
    key: str | None = pdt.Field(default=None)
    value: str | None = pdt.Field(default=None)

    @classmethod
    def from_bytes(cls, value: bytes) -> "Operation":
        ops = value.decode("utf-8")
        return cls.from_string(ops)

    @classmethod
    def from_string(cls, value: str):
        ops = value.split(" ")
        command = ops[0]
        if len(ops) == 1:
            op_key = None
            op_value = None
        elif len(ops) == 2:
            op_key = ops[1]
            op_value = None
        elif len(ops) == 3:
            op_key = ops[1]
            op_value = ops[2]
        else:
            raise ValueError(f"Invalid operation {ops}")
        return cls(command=command, key=op_key, value=op_value)

    def __str__(self) -> str:
        if self.key is not None and self.value is not None:
            return f"{self.command}:{self.key}={self.value}"
        elif self.key is not None:
            return f"{self.command}:{self.key}"
        else:
            return f"{self.command}"


@attrs.define()
class KVStore:
    database: dict[str, t.Any] = attrs.field(factory=dict)
    logger: StructLogger = attrs.field(factory=create_logger)

    def __attrs_post_init__(self) -> None:
        LOG_FILE.touch()
        self.logger.info("Loading database from log file", log_file=LOG_FILE)
        for line in LOG_FILE.read_text().splitlines():
            operation = Operation(**json.loads(line))
            self.execute(operation, persist=False)
        self.logger.info("Database loaded", database=self.database)

    def execute(self, op_bytes: bytes | str | Operation, *, persist: bool) -> str:
        if isinstance(op_bytes, str):
            operation = Operation.from_string(op_bytes)
        elif isinstance(op_bytes, bytes):
            operation = Operation.from_bytes(op_bytes)
        else:
            operation = op_bytes
        self.logger.info("Executing command", command=operation)
        if persist:
            with LOG_FILE.open("a") as f:
                f.write(operation.json() + "\n")
        if operation.command.lower() == "get":
            assert operation.key is not None
            return self.get(operation.key)
        elif operation.command.lower() == "set":
            assert operation.key is not None
            assert operation.value is not None
            self.set(operation.key, operation.value)
            return f"set {operation.key} to {operation.value}"
        elif operation.command.lower() == "delete":
            assert operation.key is not None
            self.delete(operation.key)
            return f"deleted {operation.key}"
        elif operation.command.lower() == "show":
            return f"database is: {str(self.database)}"
        else:
            return "Invalid command"

    def get(self, key: str) -> t.Any:
        return self.database[key]

    def set(self, key: str, value: t.Any) -> None:
        self.database[key] = value

    def delete(self, key: str) -> None:
        del self.database[key]

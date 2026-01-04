import asyncio
import sqlite3
import time
from dataclasses import dataclass
from typing import List


class RecvPool:
    """Pool of received BLE packets.

    Provides methods to insert, delete, and query received packets.
    Entries are automatically cleared after a configurable duration.

    Attributes:
        __sql (sqlite3.Connection): In-memory SQLite database storing packets.
        __clear_garbage_after (int): Seconds before old packets are automatically removed.
    """

    def __init__(self, clear_garbage_after: int = 60) -> None:
        """Initializes a RecvPool instance.

        Args:
            clear_garbage_after (int, optional): Seconds to keep entries in the pool. Defaults to 60.
        """

        self.__sql: sqlite3.Connection = sqlite3.connect(":memory:")
        self.__clear_garbage_after: int = clear_garbage_after

        self.__sql.execute(
            "CREATE TABLE pool ("
            "   ts INTEGER NOT NULL,"
            "   cmd_id INTEGER NOT NULL,"
            "   cmd TEXT NOT NULL,"
            "   raw BLOB NOT NULL,"
            "   UNIQUE(cmd_id, cmd, raw)"
            ");"
        )

    def __clear_garbage(self) -> None:
        """Deletes entries older than the configured duration.

        Entries older than `__clear_garbage_after` seconds are removed from the pool.
        """

        t = time.time() - self.__clear_garbage_after

        self.__sql.execute("DELETE FROM pool WHERE ts<?;", (t,))

    def insert_object(self, obj: RecvObject) -> None:
        """Inserts a RecvObject into the pool.

        Args:
            obj (RecvObject): Object to add to the pool.
        """

        self.__sql.execute(
            "INSERT OR IGNORE INTO pool (ts, cmd_id, cmd, raw) VALUES (?,?,?,?);",
            (obj.timestamp, obj.cmd_id, obj.cmd, obj.raw)
        )

        self.__clear_garbage()

    def delete_object(self, obj: RecvObject) -> None:
        """Deletes a RecvObject from the pool.

        Args:
            obj (RecvObject): Object to remove from the pool.
        """

        self.__sql.execute(
            "DELETE FROM pool WHERE ts=? AND cmd_id=? AND cmd=? AND raw=?;",
            (obj.timestamp, obj.cmd_id, obj.cmd, obj.raw)
        )

        self.__clear_garbage()

    def clear_by_command(self, command_name: str) -> None:
        """Deletes all objects in the pool matching a command name.

        Args:
            command_name (str): Command name used to filter objects for deletion.
        """

        self.__sql.execute(
            "DELETE FROM pool WHERE cmd=?;",
            (command_name,)
        )

        self.__clear_garbage()

    def get_object_by_cmd(self, cmd: str) -> List[RecvObject]:
        """Returns all objects matching a command name.

        Args:
            cmd (str): Command name to filter objects.

        Returns:
            List[RecvObject]: List of matching RecvObjects currently in the pool.
        """

        self.__clear_garbage()

        c = self.__sql.execute("SELECT ts, raw FROM pool WHERE cmd=?;", (cmd,))

        return [RecvObject(ts, raw) for ts, raw in c.fetchall()]

    def get_object_by_cmd_id(self, cmd_id: int) -> List[RecvObject]:
        """Returns all objects matching a command ID.

        Args:
            cmd_id (int): Command ID to filter objects.

        Returns:
            List[RecvObject]: List of matching RecvObjects currently in the pool.
        """

        self.__clear_garbage()

        c = self.__sql.execute("SELECT ts, raw FROM pool WHERE cmd_id=?;", (cmd_id,))

        return [RecvObject(ts, raw) for ts, raw in c.fetchall()]

    def get_object_by_cmd_id_and_cmd(self, cmd_id: int, cmd_name: str) -> List[RecvObject]:
        """Returns all objects matching both a command ID and command name.

        Args:
            cmd_id (int): Command ID to filter objects.
            cmd_name (str): Command name to filter objects.

        Returns:
            List[RecvObject]: List of matching RecvObjects currently in the pool.
        """

        self.__clear_garbage()

        c = self.__sql.execute(
            "SELECT ts, raw FROM pool WHERE cmd=? AND cmd_id=?;",
            (cmd_name, cmd_id)
        )

        return [RecvObject(ts, raw) for ts, raw in c.fetchall()]

    async def wait_for_responses(self, cmd_id: int, cmd: str, timeout: float = 0.75,
                                 is_broadcast: bool = False) -> bool:
        """Waits for at least one response to a command.

        Busy-waits until a matching packet is received or the timeout expires.
        For broadcast commands, waits the full timeout duration.

        Args:
            cmd_id (int): Command ID of the issued command.
            cmd (str): Command name of the issued command.
            timeout (float, optional): Maximum time to wait in seconds. Defaults to 0.75.
            is_broadcast (bool, optional): If True, waits full timeout even if a response is received.

        Returns:
            bool: True if at least one matching packet was received, False if timeout expired.
        """

        query = "SELECT COUNT(cmd_id) FROM pool WHERE cmd_id=? AND cmd=?;"

        if is_broadcast:
            await asyncio.sleep(timeout)

        else:
            t = time.time() + timeout

            while time.time() < t and self.__sql.execute(query, (cmd_id, cmd)).fetchone()[0] == 0:
                await asyncio.sleep(0.01)

        return self.__sql.execute(query, (cmd_id, cmd)).fetchone()[0] != 0


@dataclass
class RecvObject:
    """Represents a received message.

    Attributes:
        timestamp (int): Timestamp when the message was received.
        cmd_id (int): Command ID extracted from the raw packet.
        cmd (str): Command name extracted from the raw packet.
        data (List[str]): Strings parsed from the raw packet, following the command name.
        raw (bytes): The original raw packet.
    """

    timestamp: int  # The timestamp when the message got received

    cmd_id: int  # The command ID
    cmd: str  # The command
    data: List[str]  # All data from a command

    raw: bytes  # The raw message

    def __init__(self, timestamp: int, raw: bytes) -> None:
        """Initializes a RecvObject instance.

        Parses the raw packet to populate cmd_id, cmd, and data.

        Args:
            timestamp (int): Timestamp when the packet was received.
            raw (bytes): Raw bytes of the received packet.
        """

        self.timestamp = timestamp
        self.cmd_id = int(raw[0])
        self.cmd = raw.split(b" ")[0][1:].decode(errors="ignore")
        self.data = raw.decode(errors="ignore").split(" ")[1:]
        self.raw = raw

    def __str__(self) -> str:
        """Returns a human-readable string of the object.

        Includes timestamp, command ID, command name, and parsed data.

        Returns:
            str: Formatted string representing the object.
        """

        return f"<RecvObject ts={self.timestamp} cmd_id={self.cmd_id} cmd={self.cmd} data={self.data}>"

    def __repr__(self) -> str:
        """Returns the official string representation of the object.

        Delegates to `__str__`.

        Returns:
            str: Same as `__str__`.
        """

        return self.__str__()

    def __eq__(self, other: object):
        """Check if two RecvObject instances are equal.

        Equality is based on the `raw` attribute.

        Args:
            other (object): The object to compare with.

        Returns:
            bool: True if `other` is a `RecvObject` and has the same `raw` value, False otherwise.

        Raises:
            TypeError: If `other` is not a `RecvObject`.
        """

        if not isinstance(other, RecvObject):
            raise TypeError("Left hand object isn't a RecvObject")

        return self.raw == other.raw

import asyncio
import sqlite3
from dataclasses import dataclass
import time
from typing import List


class RecvPoll:
    """
    Class used to represent the poll of callbacks
    """

    def __init__(self, clear_garbage_after: int = 60) -> None:
        """
        :param clear_garbage_after: Defines for how long we should keep items after they are being received (in seconds)
        """

        self.__sql: sqlite3.Connection = sqlite3.connect(":memory:")
        self.__clear_garbage_after = clear_garbage_after

        self.__sql.execute(
            "CREATE TABLE poll ("
            "   ts INTEGER NOT NULL,"
            "   cmd_id INTEGER NOT NULL,"
            "   cmd TEXT NOT NULL,"
            "   raw BLOB NOT NULL,"
            "   UNIQUE(ts, cmd_id, cmd, raw)"
            ");"
        )

    def __clear_garbage(self) -> None:
        """
        Clear garbage currently in poll
        :return: None
        """

        t = time.time() - self.__clear_garbage_after

        self.__sql.execute("DELETE FROM poll WHERE ts<?;", (t,))

    def insert_object(self, obj: RecvObject) -> None:
        """
        Insert an object in poll
        :param obj: The RecvObj to add
        :return: None
        """

        self.__sql.execute(
            "INSERT OR IGNORE INTO poll (ts, cmd_id, cmd, raw) VALUES (?,?,?,?);",
            (obj.timestamp, obj.cmd_id, obj.cmd, obj.raw)
        )

        self.__clear_garbage()

    def remove_object(self, obj: RecvObject) -> None:
        """
        Remove an object from poll
        :param obj: The RecvObj to remove
        :return: None
        """

        self.__sql.execute(
            "REMOVE FROM poll WHERE ts=? AND cmd_id=? AND cmd=? AND raw=?;",
            (obj.timestamp, obj.cmd_id, obj.cmd, obj.raw)
        )

        self.__clear_garbage()

    def get_object_by_cmd(self, cmd: str) -> List[RecvObject]:
        """
        Get an object from poll by a command

        :param cmd: The command to filter from
        :return: A list of RecvObject corresponding this command
        """

        self.__clear_garbage()

        c = self.__sql.execute("SELECT ts, raw FROM poll WHERE cmd=?;", (cmd,))

        return [RecvObject(ts, raw) for ts, raw in c.fetchall()]

    def get_object_by_cmd_id(self, cmd_id: int) -> List[RecvObject]:
        """
        Get an object from poll by a command ID

        :param cmd_id: The command ID to filter from
        :return: A list of RecvObject corresponding this command ID
        """

        self.__clear_garbage()

        c = self.__sql.execute("SELECT ts, raw FROM poll WHERE cmd_id=?;", (cmd_id,))

        return [RecvObject(ts, raw) for ts, raw in c.fetchall()]

    def get_object_by_cmd_id_and_cmd(self, cmd_id: int, cmd_name: str) -> List[RecvObject]:
        """
        Get an object from poll by a command ID and a command name

        :param cmd_id: The command ID to filter from
        :param cmd_name: The command to filter from
        :return: A list of RecvObject corresponding this command and command ID
        """

        self.__clear_garbage()

        c = self.__sql.execute(
            "SELECT ts, raw FROM poll WHERE cmd=? AND cmd_id=?;",
            (cmd_name, cmd_id)
        )

        return [RecvObject(ts, raw) for ts, raw in c.fetchall()]

    async def wait_for_polling(self, cmd_id: int, cmd: str, timeout: float = 0.5, is_broadcast: bool = False) -> bool:
        """
        Method used to wait until a command polled its responses
        :param cmd_id: The command id of this command
        :param cmd: The command itself
        :param timeout: Timeout to stop listening after (in seconds)
                        If your command was a broadcast, listen for exactly timeout time
        :param is_broadcast: Define if your command was a broadcast
        :return: True if your command polled responses in the timeout, else False
        """

        query = "SELECT COUNT(cmd_id) FROM poll WHERE cmd_id=? AND cmd=?;"

        if is_broadcast:
            await asyncio.sleep(timeout)

        else:
            t = time.time() + timeout

            while time.time() < t and self.__sql.execute(query, (cmd_id, cmd)).fetchone()[0] == 0:
                await asyncio.sleep(0.01)

        return self.__sql.execute(query, (cmd_id, cmd)).fetchone()[0] != 0


@dataclass
class RecvObject:
    """
    Object used to represent a received message
    """

    timestamp: int   # The timestamp when the message got received

    cmd_id: int      # The command ID
    cmd: str         # The command
    args: List[str]  # All arguments from a command

    raw: bytes       # The raw message

    def __init__(self, timestamp: int, raw: bytes):
        self.timestamp = timestamp
        self.cmd_id = int(raw[0])
        self.cmd = raw.split(b" ")[0][1:].decode(errors="ignore")
        self.args = raw.decode(errors="ignore").split(" ")[1:]
        self.raw = raw

    def __str__(self) -> str:
        return f"<RecvObject ts={self.timestamp} cmd_id={self.cmd_id} cmd={self.cmd} args={self.args}>"

    def __repr__(self) -> str:
        return self.__str__()

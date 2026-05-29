from __future__ import annotations

import re
import time
from typing import Callable

import serial
from serial.tools import list_ports

FLIPPER_USB_VID = 0x0483
FLIPPER_USB_PIDS = {0x5740, 0x5741}
PROMPT_RE = re.compile(r">:\s*$", re.MULTILINE)
READY_RE = re.compile(r"Ready\r?\n", re.MULTILINE)
STAT_SIZE_RE = re.compile(r"File, size:\s*(\d+)b", re.IGNORECASE)
CHUNK_SIZE = 8192


class FlipperNotFoundError(RuntimeError):
    pass


class FlipperSerialError(RuntimeError):
    pass


def find_flipper_port(explicit: str | None = None) -> str:
    if explicit:
        return explicit
    matches: list[str] = []
    for info in list_ports.comports():
        if info.vid == FLIPPER_USB_VID and (info.pid in FLIPPER_USB_PIDS or info.pid is None):
            if info.device:
                matches.append(info.device)
    if not matches:
        raise FlipperNotFoundError(
            "No Flipper USB serial port found (VID 0483). "
            "Plug in USB, exit Storage/BadUSB mode, close qFlipper, then set flipper_port in config."
        )
    if len(matches) > 1:
        raise FlipperNotFoundError(
            f"Multiple Flipper serial ports found: {', '.join(matches)}. "
            "Set flipper_port in ~/.config/ck42x-pl-arch/config.json"
        )
    return matches[0]


class FlipperCli:
    """Flipper Zero CLI over USB serial (same protocol as ck42x.com Payload Bay flasher)."""

    def __init__(self, port: str, baud: int = 115200) -> None:
        self.port = port
        self._ser = serial.Serial(port, baud, timeout=0.25)
        self._buffer = ""

    def close(self) -> None:
        if self._ser.is_open:
            self._ser.close()

    def __enter__(self) -> FlipperCli:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    @classmethod
    def connect(cls, port: str | None = None, baud: int = 115200) -> FlipperCli:
        device = find_flipper_port(port)
        cli = cls(device, baud)
        cli._wake()
        try:
            cli.command("loader close", timeout=4.0)
        except FlipperSerialError:
            pass
        return cli

    def _read_into_buffer(self) -> None:
        waiting = self._ser.in_waiting
        data = self._ser.read(waiting or 1)
        if data:
            self._buffer += data.decode("utf-8", errors="replace")

    def _wait_for(self, pattern: re.Pattern[str], timeout: float) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self._read_into_buffer()
            if pattern.search(self._buffer):
                return
            time.sleep(0.04)
        tail = self._buffer[-500:]
        raise FlipperSerialError(f"Timed out waiting for {pattern.pattern!r}. Last output: {tail!r}")

    def _wake(self) -> None:
        self._buffer = ""
        self._ser.write(b"\r")
        try:
            self._wait_for(PROMPT_RE, 4.0)
        except FlipperSerialError:
            self._ser.write(b"\r")
            self._wait_for(PROMPT_RE, 4.0)

    def command(self, cmd: str, timeout: float = 6.0) -> str:
        self._buffer = ""
        self._ser.write(f"{cmd}\r".encode("utf-8"))
        self._wait_for(PROMPT_RE, timeout)
        return self._buffer

    def mkdir(self, path: str) -> None:
        try:
            self.command(f'storage mkdir "{path}"', timeout=4.0)
        except FlipperSerialError:
            pass

    def write_file(
        self,
        destination: str,
        data: bytes,
        *,
        label: str | None = None,
        on_progress: Callable[[int, int], None] | None = None,
    ) -> None:
        label = label or destination
        try:
            self.command(f'storage remove "{destination}"', timeout=4.0)
        except FlipperSerialError:
            pass

        for offset in range(0, len(data), CHUNK_SIZE):
            chunk = data[offset : offset + CHUNK_SIZE]
            self._buffer = ""
            self._ser.write(f'storage write_chunk "{destination}" {len(chunk)}\r'.encode("utf-8"))
            self._wait_for(READY_RE, 5.0)
            self._buffer = ""
            self._ser.write(chunk)
            self._wait_for(PROMPT_RE, 12.0)
            written = offset + len(chunk)
            if on_progress:
                on_progress(written, len(data))

        stat = self.command(f'storage stat "{destination}"', timeout=5.0)
        match = STAT_SIZE_RE.search(stat)
        installed = int(match.group(1)) if match else None
        if installed != len(data):
            raise FlipperSerialError(
                f"{label} size mismatch: expected {len(data)} bytes, Flipper reports {installed!r}."
            )

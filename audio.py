"""Windows native audio playback with the device position as the master clock.

The playback module uses only Python's standard library.  Analysis and FLAC
decoding are performed separately by prepare_assets.py.
"""

from __future__ import annotations

import ctypes
import os
from pathlib import Path
import uuid
import wave


class _MCIError(RuntimeError):
    def __init__(self, code: int, detail: str):
        self.code = code
        super().__init__(f"Windows 音频播放失败（{code}）：{detail}")


class AudioPlayer:
    """Play a PCM WAV file through Windows MCI (waveaudio).

    All times are seconds.  ``position()`` queries winmm directly; it never
    extrapolates from a wall clock.  MCI reports position in integer milliseconds.
    A newly constructed player is paused and starts only on ``play()``/``resume()``.
    """

    backend = "Windows MCI waveaudio"
    clock_resolution = 0.001

    def __init__(self, path: str | os.PathLike[str]):
        if os.name != "nt":
            raise RuntimeError("音频播放目前仅支持 Windows；请使用静音预览模式。")
        self.path = Path(path).resolve()
        if not self.path.is_file():
            raise FileNotFoundError(f"找不到音乐缓存：{self.path}；请先运行 prepare_assets.py。")
        try:
            with wave.open(str(self.path), "rb") as stream:
                frames = stream.getnframes()
                if frames <= 0 or stream.getsampwidth() != 2:
                    raise RuntimeError("音乐缓存没有可播放的 PCM16 音频帧；请重新运行 prepare_assets.py。")
                stream.setpos(frames - 1)
                if len(stream.readframes(1)) != stream.getnchannels() * stream.getsampwidth():
                    raise RuntimeError("音乐缓存已截短；请重新运行 prepare_assets.py。")
                self.duration = frames / stream.getframerate()
        except (wave.Error, EOFError) as exc:
            raise RuntimeError(f"音乐缓存不是可播放的 PCM WAV 文件：{self.path}") from exc
        self.paused = True
        self._closed = False
        self._alias = "amara_" + uuid.uuid4().hex
        self._winmm = ctypes.WinDLL("winmm")
        self._winmm.mciSendStringW.argtypes = (
            ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint, ctypes.c_void_p
        )
        self._winmm.mciSendStringW.restype = ctypes.c_uint
        self._winmm.mciGetErrorStringW.argtypes = (
            ctypes.c_uint, ctypes.c_wchar_p, ctypes.c_uint
        )
        self._winmm.mciGetErrorStringW.restype = ctypes.c_int
        try:
            self._command(f'open "{self.path}" type waveaudio alias {self._alias}')
            self._command(f"set {self._alias} time format milliseconds")
        except Exception:
            self.close()
            raise

    def _command(self, command: str) -> str:
        if self._closed:
            raise RuntimeError("音频播放器已关闭。")
        result = ctypes.create_unicode_buffer(256)
        error = self._winmm.mciSendStringW(command, result, len(result), None)
        if error:
            message = ctypes.create_unicode_buffer(512)
            self._winmm.mciGetErrorStringW(error, message, len(message))
            detail = message.value.strip() or "未知音频设备错误"
            raise _MCIError(error, detail)
        return result.value.strip()

    def _milliseconds(self, seconds: float) -> int:
        return min(round(self.duration * 1000), max(0, round(float(seconds) * 1000)))

    def position(self) -> float:
        """Return actual audio device position, reported in MCI milliseconds."""
        value = self._command(f"status {self._alias} position")
        try:
            return min(self.duration, max(0.0, int(value) / 1000.0))
        except ValueError as exc:
            raise RuntimeError(f"音频设备返回了无效的播放位置：{value!r}") from exc

    def play(self, start: float = 0.0) -> None:
        """Start playback at the supplied position, including after completion."""
        self._command(f"play {self._alias} from {self._milliseconds(start)}")
        self.paused = False

    def pause(self) -> None:
        if not self.paused:
            # MCI rejects pause after natural completion; a stopped player is
            # already stationary and can simply acquire the paused UI state.
            if (self.position() < self.duration - 0.001
                    and self._command(f"status {self._alias} mode").lower() == "playing"):
                try:
                    self._command(f"pause {self._alias}")
                except _MCIError as exc:
                    # The final audio sample may complete between the two MCI
                    # commands.  Ignore only that documented command-order case.
                    if exc.code != 302 or self.position() < self.duration - 0.001:
                        raise
            self.paused = True

    def resume(self) -> None:
        if self.paused:
            self._command(f"play {self._alias}")
            self.paused = False

    def seek(self, t: float) -> None:
        """Seek without changing whether playback is paused."""
        target = self._milliseconds(t)
        was_paused = self.paused
        self._command(f"seek {self._alias} to {target}")
        if not was_paused:
            self._command(f"play {self._alias}")

    def close(self) -> None:
        if not getattr(self, "_closed", True):
            # Release the native device even when initialization or playback fails.
            self._winmm.mciSendStringW(f"close {self._alias}", None, 0, None)
            self._closed = True
            self.paused = True

    def __enter__(self) -> "AudioPlayer":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


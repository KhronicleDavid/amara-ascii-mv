"""Regression checks for device-clock playback, cleanup, and cache corruption.

These tests never start music.  A scripted device clock verifies that animation
time cannot accidentally depend on rendering speed or the frame counter.
"""

from __future__ import annotations

import ctypes
import io
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
import wave

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import amara
import audio
import prepare_assets


class FakePlayer:
    duration = 195.50652083333333

    def __init__(self, positions=None):
        self.paused = True
        self.at = 0.0
        self.positions = iter(positions) if positions is not None else None
        self.closed = False
        self.actions = []

    def position(self):
        if self.positions is not None:
            self.at = next(self.positions)
        return self.at

    def play(self, start=0.0):
        self.at, self.paused = start, False
        self.actions.append(("play", start))

    def pause(self):
        self.paused = True
        self.actions.append(("pause",))

    def resume(self):
        self.paused = False
        self.actions.append(("resume",))

    def seek(self, t):
        self.at = max(0.0, min(self.duration, t))
        self.actions.append(("seek", self.at))

    def close(self):
        self.closed = True


class FakeTerminal:
    def __init__(self, keys):
        self.keys = iter(keys)
        self.entered = self.exited = False
        self.exit_type = None

    def __enter__(self):
        self.entered = True
        return self

    def __exit__(self, exception_type, *_):
        self.exited, self.exit_type = True, exception_type

    def key(self):
        return next(self.keys)


class FakeFilm:
    duration = FakePlayer.duration

    def __init__(self, failure=None):
        self.frames = []
        self.failure = failure

    def frame(self, t, width, height, offset, paused):
        if self.failure:
            raise self.failure
        self.frames.append((t, paused))
        return Mock(ansi=Mock(return_value=""))


class PlaybackLoopTests(unittest.TestCase):
    def run_loop(self, player, keys, film=None):
        film = film or FakeFilm()
        terminal = FakeTerminal(keys)
        # Deliberately advance wall time much faster than device time.
        wall = iter(float(i * 100) for i in range(200))
        with (patch.object(amara, "Film", return_value=film),
              patch.object(amara, "Terminal", return_value=terminal),
              patch.object(audio, "AudioPlayer", return_value=player),
              patch.object(amara.time, "perf_counter", side_effect=lambda: next(wall)),
              patch.object(amara.time, "sleep"),
              patch.object(amara.sys, "stdout", io.StringIO())):
            result = amara.main(["--headless", "--size", "80", "30", "--start", "10"])
        return film, terminal, result

    def test_frames_follow_actual_device_position(self):
        player = FakePlayer([10.0, 10.371, 12.910])
        film, terminal, result = self.run_loop(player, ["", "", "", "q"])
        self.assertEqual([t for t, _ in film.frames], [10.0, 10.371, 12.910])
        self.assertTrue(player.closed and terminal.exited)
        self.assertEqual(result, 0)

    def test_pause_seek_resume_restart_preserve_clock_state(self):
        player = FakePlayer()
        film, terminal, _ = self.run_loop(player, [" ", "right", " ", "r", "q"])
        self.assertEqual(film.frames, [(10.0, True), (15.0, True), (15.0, False), (0.0, False)])
        self.assertEqual(player.actions, [
            ("play", 10.0), ("pause",), ("seek", 15.0), ("resume",), ("seek", 0.0)
        ])
        self.assertTrue(player.closed and terminal.exited)

    def test_completion_uses_device_position(self):
        player = FakePlayer([FakePlayer.duration])
        film, terminal, _ = self.run_loop(player, [""])
        self.assertEqual(film.frames, [])
        self.assertTrue(player.closed and terminal.exited)

    def test_renderer_failure_releases_audio_and_terminal(self):
        player = FakePlayer()
        terminal = FakeTerminal([""])
        film = FakeFilm(RuntimeError("render failure"))
        with (patch.object(amara, "Film", return_value=film),
              patch.object(amara, "Terminal", return_value=terminal),
              patch.object(audio, "AudioPlayer", return_value=player),
              patch.object(amara.sys, "stdout", io.StringIO())):
            with self.assertRaisesRegex(RuntimeError, "render failure"):
                amara.main(["--headless", "--size", "80", "30"])
        self.assertTrue(player.closed)
        self.assertTrue(terminal.exited)
        self.assertIs(terminal.exit_type, RuntimeError)


class NativeCleanupTests(unittest.TestCase):
    def test_terminal_restores_cursor_buffer_and_console_modes(self):
        kernel = Mock()
        kernel.GetStdHandle = Mock(side_effect=lambda value: value)

        def console_mode(handle, pointer):
            pointer._obj.value = 0x57 if handle == (-11 & 0xffffffff) else 0x43
            return 1

        kernel.GetConsoleMode = Mock(side_effect=console_mode)
        kernel.SetConsoleMode = Mock(return_value=1)
        output = io.StringIO()
        with patch.object(ctypes, "WinDLL", return_value=kernel), patch.object(amara.sys, "stdout", output):
            with self.assertRaisesRegex(RuntimeError, "intentional"):
                with amara.Terminal():
                    raise RuntimeError("intentional")
        self.assertIn("\x1b[?25l", output.getvalue())
        self.assertTrue(output.getvalue().endswith("\x1b[0m\x1b[?25h\x1b[?1049l"))
        self.assertEqual(kernel.SetConsoleMode.call_args_list[-2].args, (-11 & 0xffffffff, 0x57))
        self.assertEqual(kernel.SetConsoleMode.call_args_list[-1].args, (-10 & 0xffffffff, 0x43))

    def test_pause_handles_completion_between_device_commands(self):
        player = audio.AudioPlayer.__new__(audio.AudioPlayer)
        player.duration, player.paused = 10.0, False
        player._alias = "test"
        player.position = Mock(side_effect=[9.9, 10.0])

        def command(text):
            if text == "status test mode":
                return "playing"
            raise audio._MCIError(302, "device has completed")

        player._command = Mock(side_effect=command)
        player.pause()
        self.assertTrue(player.paused)


class CacheIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = self.root / "ÅMARA fixture.flac"
        self.source.write_bytes(b"source fixture")
        self.assets = self.root / "assets"
        self.assets.mkdir()
        self.wav = self.assets / "amara.wav"
        with wave.open(str(self.wav), "wb") as stream:
            stream.setnchannels(2)
            stream.setsampwidth(2)
            stream.setframerate(48000)
            stream.writeframes(b"\0" * 4800 * 4)
        self.analysis = {
            "duration": 0.1, "sample_rate": 48000, "hop_seconds": 1 / 30,
            **{key: [0.0] * 3 for key in ["energy", "bass", "high", "onset"]},
            "meta": prepare_assets._source_identity(self.source) | {"frames": 4800, "channels": 2},
        }
        self.analysis_path = self.assets / "analysis.json"
        self.save_analysis()
        self.root_patch = patch.object(prepare_assets, "ROOT", self.root)
        self.root_patch.start()

    def tearDown(self):
        self.root_patch.stop()
        self.temporary.cleanup()

    def save_analysis(self):
        self.analysis_path.write_text(json.dumps(self.analysis), encoding="utf-8")

    def test_valid_cache_reused_without_build_dependencies(self):
        self.assertTrue(prepare_assets.inspect_assets(self.source)["valid"])
        with patch.dict(sys.modules, {"numpy": None, "soundfile": None}):
            self.assertEqual(prepare_assets.prepare_assets(self.source), (self.wav, self.analysis_path))

    def test_source_change_invalidates_cache(self):
        self.source.write_bytes(b"modified source fixture")
        self.assertFalse(prepare_assets.inspect_assets(self.source)["valid"])

    def test_truncation_with_unchanged_wave_header_is_detected(self):
        self.wav.write_bytes(self.wav.read_bytes()[:-16])
        status = prepare_assets.inspect_assets(self.source)
        self.assertFalse(status["valid"])
        self.assertTrue(any("截短" in message for message in status["errors"]))
        with self.assertRaisesRegex(RuntimeError, "截短"):
            audio.AudioPlayer(self.wav)

    def test_incomplete_or_nonfinite_feature_data_is_detected(self):
        self.analysis["onset"].pop()
        self.save_analysis()
        self.assertFalse(prepare_assets.inspect_assets(self.source)["valid"])
        self.analysis["onset"] = [math.nan, 0.0, 0.0]
        self.save_analysis()
        self.assertFalse(prepare_assets.inspect_assets(self.source)["valid"])


if __name__ == "__main__":
    unittest.main()

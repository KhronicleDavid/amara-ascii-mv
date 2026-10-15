"""Decode the supplied FLAC and derive real, frame-aligned music features.

Run once with Python + numpy + soundfile.  The terminal player needs only the
generated caches and Python's standard library afterward.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import tempfile
import wave


ROOT = Path(__file__).resolve().parent
DEFAULT_SOURCE = ROOT / "ÅMARA (大未来電脳).flac"
ASSET_VERSION = 1


def _source_identity(source_path: Path) -> dict:
    source_path = source_path.resolve()
    stat = source_path.stat()
    return {
        "version": ASSET_VERSION,
        "source": source_path.name,
        "source_path": str(source_path),
        "source_size": stat.st_size,
        "source_mtime_ns": stat.st_mtime_ns,
    }


def _cache_errors(analysis: dict, wav_path: Path, identity: dict) -> list[str]:
    """Check cache structure and WAV length using only the standard library."""
    errors = []
    if not isinstance(analysis, dict):
        return ["音乐分析缓存不是 JSON 对象。"]
    meta = analysis.get("meta")
    if not isinstance(meta, dict) or any(meta.get(k) != v for k, v in identity.items()):
        errors.append("音乐源文件已变化或缓存版本不匹配。")
        meta = meta if isinstance(meta, dict) else {}
    try:
        duration = analysis["duration"]
        sample_rate = analysis["sample_rate"]
        hop_seconds = analysis["hop_seconds"]
        if (not math.isfinite(duration) or duration <= 0
                or not isinstance(sample_rate, int) or sample_rate <= 0
                or not math.isfinite(hop_seconds) or hop_seconds <= 0):
            raise ValueError
        # Avoid an extra frame when a mathematically integral quotient is
        # represented as e.g. 3.0000000000000004 in binary floating point.
        expected_count = math.ceil(duration / hop_seconds - 1e-9)
        for key in ("energy", "bass", "high", "onset"):
            values = analysis[key]
            if (not isinstance(values, list) or len(values) != expected_count
                    or any(not isinstance(v, (int, float)) or not math.isfinite(v)
                           or not 0 <= v <= 1 for v in values)):
                raise ValueError
    except (KeyError, TypeError, ValueError, OverflowError):
        errors.append("音乐分析缓存的时长、帧数或特征数据不完整。")
        duration = sample_rate = None
    try:
        with wave.open(str(wav_path), "rb") as stream:
            frames, rate = stream.getnframes(), stream.getframerate()
            channels, width = stream.getnchannels(), stream.getsampwidth()
            if (width != 2 or frames != meta.get("frames")
                    or channels != meta.get("channels") or rate != sample_rate
                    or duration is None or abs(frames / rate - duration) > 1 / rate):
                errors.append("WAV 缓存的格式或实际音频长度与音乐分析不一致。")
            # A truncated RIFF can retain its original header, so also check that
            # the advertised final PCM frame is physically present in the file.
            if frames:
                stream.setpos(frames - 1)
                if len(stream.readframes(1)) != channels * width:
                    errors.append("WAV 缓存已截短，缺少音频数据。")
    except (OSError, wave.Error, EOFError, ZeroDivisionError):
        errors.append("WAV 音频缓存缺失或损坏。")
    return errors


def inspect_assets(source: str | os.PathLike[str] | None = None) -> dict:
    """Read-only, stdlib cache validation, suitable for runtime diagnostics."""
    source_path = Path(source).resolve() if source is not None else DEFAULT_SOURCE
    wav_path = ROOT / "assets" / "amara.wav"
    analysis_path = ROOT / "assets" / "analysis.json"
    try:
        identity = _source_identity(source_path)
        analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
        errors = _cache_errors(analysis, wav_path, identity)
    except FileNotFoundError as exc:
        errors = [f"音乐源文件或缓存缺失：{exc.filename}"]
        analysis = {}
    except (OSError, ValueError) as exc:
        errors = [f"无法读取音乐分析缓存：{exc}"]
        analysis = {}
    return {
        "valid": not errors,
        "errors": errors,
        "wav_path": str(wav_path),
        "analysis_path": str(analysis_path),
        "duration": analysis.get("duration") if isinstance(analysis, dict) else None,
    }


def _normalized(values, np):
    """Robustly scale musical features without amplifying digital silence."""
    ceiling = float(np.percentile(values, 99.5))
    if ceiling <= 1e-12:
        return np.zeros_like(values)
    return np.clip(values / ceiling, 0.0, 1.0)


def _atomic_json(path: Path, content: dict) -> None:
    fd, temporary = tempfile.mkstemp(prefix="amara-analysis-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(content, stream, ensure_ascii=False, separators=(",", ":"))
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def prepare_assets(source: str | os.PathLike[str] | None = None, force: bool = False):
    """Return (WAV path, analysis path), rebuilding only when source changes."""
    source_path = Path(source).resolve() if source is not None else DEFAULT_SOURCE
    if not source_path.is_file():
        raise FileNotFoundError(f"找不到音乐源文件：{source_path}")
    assets = ROOT / "assets"
    assets.mkdir(exist_ok=True)
    wav_path = assets / "amara.wav"
    analysis_path = assets / "analysis.json"
    identity = _source_identity(source_path)
    if not force and wav_path.is_file() and analysis_path.is_file():
        try:
            old = json.loads(analysis_path.read_text(encoding="utf-8"))
            if not _cache_errors(old, wav_path, identity):
                return wav_path, analysis_path
        except (OSError, ValueError):
            pass

    try:
        import numpy as np
        import soundfile as sf
    except ImportError as exc:
        raise RuntimeError("准备音乐缓存需要 numpy 和 soundfile；请使用已安装这些库的 Python。") from exc

    samples, sample_rate = sf.read(str(source_path), dtype="float32", always_2d=True)
    frame_count, channels = samples.shape
    if frame_count == 0:
        raise RuntimeError("音乐源文件没有音频帧。")

    # Do not touch or rename the original FLAC.  Write a temporary WAV first.
    fd, temporary = tempfile.mkstemp(prefix="amara-wave-", suffix=".wav", dir=assets)
    os.close(fd)
    try:
        sf.write(temporary, samples, sample_rate, subtype="PCM_16", format="WAV")
        os.replace(temporary, wav_path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

    # Center one FFT window on each rendered animation frame.  RMS uses all
    # channels, avoiding cancellation when stereo content is out of phase.
    hop = max(1, round(sample_rate / 30))
    window_size = 2 ** math.ceil(math.log2(max(1024, sample_rate / 12)))
    count = math.ceil(frame_count / hop)
    centers = np.arange(count, dtype=np.int64) * hop
    window = np.hanning(window_size).astype(np.float32)
    offsets = np.arange(window_size, dtype=np.int64) - window_size // 2
    frequencies = np.fft.rfftfreq(window_size, 1 / sample_rate)
    bass_mask = (frequencies >= 30) & (frequencies <= 220)
    high_mask = (frequencies >= 3000) & (frequencies <= min(14000, sample_rate * 0.49))
    energy = np.empty(count, dtype=np.float32)
    bass = np.empty(count, dtype=np.float32)
    high = np.empty(count, dtype=np.float32)
    onset = np.empty(count, dtype=np.float32)
    previous_spectrum = None

    for first in range(0, count, 128):
        last = min(count, first + 128)
        indices = centers[first:last, None] + offsets[None, :]
        valid = (indices >= 0) & (indices < frame_count)
        frames = samples[np.clip(indices, 0, frame_count - 1)]
        frames *= valid[..., None]
        energy[first:last] = np.sqrt(np.mean(frames * frames, axis=(1, 2)))
        spectrum = np.fft.rfft(frames * window[None, :, None], axis=1)
        magnitude = np.sqrt(np.mean(np.abs(spectrum) ** 2, axis=2))
        bass[first:last] = np.sqrt(np.mean(magnitude[:, bass_mask] ** 2, axis=1))
        high[first:last] = np.sqrt(np.mean(magnitude[:, high_mask] ** 2, axis=1))
        # Positive spectral flux captures percussion/transients across bands.
        logged = np.log1p(magnitude)
        if previous_spectrum is None:
            previous_spectrum = logged[0]
        comparison = np.concatenate([previous_spectrum[None, :], logged[:-1]], axis=0)
        onset[first:last] = np.mean(np.maximum(logged - comparison, 0.0), axis=1)
        previous_spectrum = logged[-1]

    metadata = identity | {
        "frames": frame_count,
        "channels": channels,
        "wav_subtype": "PCM_16",
        "fft_window": window_size,
        "bass_hz": [30, 220],
        "high_hz": [3000, min(14000, sample_rate * 0.49)],
    }
    analysis = {
        "duration": frame_count / sample_rate,
        "sample_rate": sample_rate,
        "hop_seconds": hop / sample_rate,
        "energy": np.round(_normalized(energy, np), 5).tolist(),
        "bass": np.round(_normalized(bass, np), 5).tolist(),
        "high": np.round(_normalized(high, np), 5).tolist(),
        "onset": np.round(_normalized(onset, np), 5).tolist(),
        "meta": metadata,
    }
    _atomic_json(analysis_path, analysis)
    return wav_path, analysis_path


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 ÅMARA 播放缓存与音乐响应数据。")
    parser.add_argument("source", nargs="?", help="可选：FLAC 源文件路径")
    parser.add_argument("--force", action="store_true", help="强制重建缓存")
    options = parser.parse_args()
    try:
        wav_path, analysis_path = prepare_assets(options.source, options.force)
        metadata = json.loads(analysis_path.read_text(encoding="utf-8"))
        print(f"音乐缓存已就绪：{wav_path}")
        print(f"分析数据已就绪：{analysis_path}")
        print(f"时长 {metadata['duration']:.3f} 秒；采样率 {metadata['sample_rate']} Hz；分析 {len(metadata['energy'])} 帧。")
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"准备失败：{exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

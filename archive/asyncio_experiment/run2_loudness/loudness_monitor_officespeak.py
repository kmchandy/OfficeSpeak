"""
loudness_monitor — OfficeSpeak-style, sequential (no gather, no LLM).

Pat's spec: watch an audio stream, compute loudness (RMS/dBFS) over short
chunks, and alert when loudness crosses a threshold (edge-triggered with
debounce).

This is the OfficeSpeak "Run 2" form of the app: a `SOURCES` dict, one
stateful agent per stage (`process(self, message)`), and a `process_one`
whose control flow *is* the pipeline. The two agents run in sequence —
there is no `asyncio.gather` and no post-merge conditional — so this
exercises the plain source → A → B → sink dataflow that a faithful
translator produces directly from the control flow.
"""

from __future__ import annotations

import asyncio
import math


# A registered chunked-audio source. `paced=False` runs as fast as
# possible so the demo doesn't take the clip's real duration.
SOURCES = {
    "mic": audio_clip(
        path="./samples/thunderstorm.wav",
        chunk_ms=200,
        paced=False,
    ),
}


class RMSMeter:
    """Compute RMS + dBFS loudness for each inbound audio chunk."""

    def __init__(self):
        self._epsilon = 1e-10

    def process(self, message):
        """Attach 'db' and 'rms' to one audio chunk."""
        import numpy as np
        samples = message.get("samples")
        if samples is None:
            return None
        arr = np.asarray(samples, dtype=float).flatten()
        if arr.size == 0:
            return None
        rms = float(np.sqrt(np.mean(arr * arr)))
        db = 20.0 * math.log10(max(rms, self._epsilon))
        return {
            "db": db,
            "rms": rms,
            "timestamp": message.get("timestamp"),
            "chunk_index": message.get("chunk_index"),
            "stream_position_seconds": message.get("stream_position_seconds"),
        }


class ThresholdDetector:
    """Emit an event only on the rising edge above a dB threshold."""

    def __init__(self, db_threshold: float = -30.0, debounce_ms: float = 400.0):
        self.db_threshold = float(db_threshold)
        self.debounce_ms = float(debounce_ms)
        self._armed = True
        self._below_since = None
        self._count = 0

    def process(self, message):
        """Return an event dict on a rising edge, else None."""
        db = message.get("db")
        ts = message.get("timestamp") or 0.0
        pos = message.get("stream_position_seconds")
        if db is None:
            return None

        if db >= self.db_threshold:
            self._below_since = None
            if self._armed:
                self._armed = False
                self._count += 1
                return {
                    "event": "loud",
                    "event_index": self._count,
                    "peak_db": db,
                    "stream_position_seconds": pos,
                    "title": f"Loud event at {pos}",
                    "text": f"Event #{self._count} — peak {db:+.1f} dBFS",
                    "source": "loudness_monitor",
                }
        else:
            if not self._armed:
                if self._below_since is None:
                    self._below_since = ts
                elif (ts - self._below_since) * 1000.0 >= self.debounce_ms:
                    self._armed = True
                    self._below_since = None
        return None


meter = RMSMeter()
detector = ThresholdDetector(db_threshold=-30.0, debounce_ms=400.0)


async def process_one(chunk):
    """Per-chunk pipeline: measure loudness, detect loud events, display them.

    Two sequential stages. The detector returns None for ordinary chunks,
    so only the rising-edge events reach the terminal — the "respond"
    half lives in the agent, not in this control flow.
    """
    loudness = meter.process(chunk)
    event = detector.process(loudness)
    send_to(event, "terminal")
    return event


async def main():
    pass

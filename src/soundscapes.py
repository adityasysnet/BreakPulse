import io
import math
import random
import struct
import sys
import threading
import wave
from typing import Dict, Optional

if sys.platform == "win32":
    import winsound
else:
    winsound = None

class SoundscapesManager:
    """
    Synthesizes and loops zero-overhead ambient background soundscapes (Brown Noise, Rain, White Noise, Lofi Tick).
    Runs 100% in-memory using standard library Windows audio with zero external dependencies.
    """
    def __init__(self):
        self.current_sound: Optional[str] = None
        self.is_playing: bool = False
        self._cache: Dict[str, bytes] = {}
        self._lock = threading.Lock()

    def _generate_brown_noise(self, duration: float = 4.0, sample_rate: int = 22050) -> bytes:
        num_samples = int(duration * sample_rate)
        samples = bytearray()
        last = 0.0
        for _ in range(num_samples):
            white = (random.random() * 2.0 - 1.0)
            last = (last + (0.02 * white)) / 1.02
            clamped = max(-1.0, min(1.0, last * 3.2))
            val = int(clamped * 32767 * 0.35)
            samples.extend(struct.pack("<h", val))
        return self._wrap_wav(samples, sample_rate)

    def _generate_white_noise(self, duration: float = 3.0, sample_rate: int = 22050) -> bytes:
        num_samples = int(duration * sample_rate)
        samples = bytearray()
        for _ in range(num_samples):
            white = (random.random() * 2.0 - 1.0) * 0.15
            val = int(white * 32767)
            samples.extend(struct.pack("<h", val))
        return self._wrap_wav(samples, sample_rate)

    def _generate_rain(self, duration: float = 4.0, sample_rate: int = 22050) -> bytes:
        num_samples = int(duration * sample_rate)
        samples = bytearray()
        last = 0.0
        for i in range(num_samples):
            # Base brown noise
            white = (random.random() * 2.0 - 1.0)
            last = (last + (0.025 * white)) / 1.02
            base = last * 2.2

            # Random gentle rain droplets (high frequencies)
            if random.random() < 0.035:
                droplet = (random.random() * 0.45)
            else:
                droplet = 0.0

            mix = max(-1.0, min(1.0, (base * 0.7 + droplet * 0.3)))
            val = int(mix * 32767 * 0.32)
            samples.extend(struct.pack("<h", val))
        return self._wrap_wav(samples, sample_rate)

    def _generate_lofi_tick(self, duration: float = 2.0, sample_rate: int = 22050) -> bytes:
        num_samples = int(duration * sample_rate)
        samples = bytearray()
        # 1 tick per second (at t=0 and t=1.0)
        for i in range(num_samples):
            t = (i % sample_rate) / sample_rate
            if t < 0.03:
                # High-frequency damped wood click
                decay = math.exp(-120.0 * t)
                val_float = math.sin(2.0 * math.pi * 1200.0 * t) * decay * 0.35
            else:
                val_float = 0.0
            val = int(val_float * 32767)
            samples.extend(struct.pack("<h", val))
        return self._wrap_wav(samples, sample_rate)

    def _wrap_wav(self, raw_samples: bytearray, sample_rate: int) -> bytes:
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            wav.writeframes(raw_samples)
        return buf.getvalue()

    def get_sound_buffer(self, sound_name: str) -> Optional[bytes]:
        with self._lock:
            if sound_name in self._cache:
                return self._cache[sound_name]

            if sound_name == "brown_noise":
                data = self._generate_brown_noise()
            elif sound_name == "rain":
                data = self._generate_rain()
            elif sound_name == "white_noise":
                data = self._generate_white_noise()
            elif sound_name == "lofi_tick":
                data = self._generate_lofi_tick()
            else:
                return None

            self._cache[sound_name] = data
            return data

    def play(self, sound_name: str):
        if not winsound:
            return

        data = self.get_sound_buffer(sound_name)
        if not data:
            return

        def _worker():
            try:
                # Stop existing sound
                winsound.PlaySound(None, 0)
                # Play seamless loop asynchronously
                winsound.PlaySound(
                    data,
                    winsound.SND_MEMORY | winsound.SND_ASYNC | winsound.SND_LOOP
                )
            except Exception as e:
                print(f"[Soundscapes] Play error: {e}")

        self.current_sound = sound_name
        self.is_playing = True
        threading.Thread(target=_worker, daemon=True).start()

    def stop(self):
        if not winsound:
            return
        try:
            winsound.PlaySound(None, 0)
        except Exception:
            pass
        self.is_playing = False
        self.current_sound = None

    def toggle(self, sound_name: str) -> bool:
        """Toggles a sound on or off. Returns True if now playing, False if stopped."""
        if self.is_playing and self.current_sound == sound_name:
            self.stop()
            return False
        else:
            self.play(sound_name)
            return True

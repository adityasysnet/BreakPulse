import io
import math
import struct
import wave
import threading
import sys

# Only windows has winsound
if sys.platform == "win32":
    import winsound
else:
    winsound = None

class AudioManager:
    """
    Self-contained, zero-dependency audio generator and player.
    Synthesizes smooth harmonic chime sounds in-memory using Python's standard library.
    """
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._sound_cache = {}
        self._pregenerate_sounds()

    def set_enabled(self, enabled: bool):
        self.enabled = enabled

    def _generate_sine_chime_wav(self, frequencies: list[float], duration: float = 1.2, sample_rate: int = 44100) -> bytes:
        """Synthesizes an elegant ambient chime chord with exponential decay."""
        num_samples = int(duration * sample_rate)
        buffer = io.BytesIO()

        with wave.open(buffer, "wb") as wav:
            wav.setnchannels(1)  # Mono
            wav.setsampwidth(2)  # 16-bit
            wav.setframerate(sample_rate)

            samples = bytearray()
            for i in range(num_samples):
                t = i / sample_rate
                # Envelope: rapid attack, gentle exponential decay
                decay = math.exp(-3.5 * t)
                if t < 0.02:
                    attack = t / 0.02
                else:
                    attack = 1.0
                envelope = attack * decay

                # Sum harmonics
                val = 0.0
                for idx, freq in enumerate(frequencies):
                    weight = 1.0 / (idx + 1)
                    val += weight * math.sin(2.0 * math.pi * freq * t)

                # Normalize and scale to 16-bit signed integer
                val = val * envelope * 0.45
                clamped = max(-1.0, min(1.0, val))
                sample_val = int(clamped * 32767)
                samples.extend(struct.pack("<h", sample_val))

            wav.writeframes(samples)

        return buffer.getvalue()

    def _pregenerate_sounds(self):
        try:
            # 1. Break Start Chime (Gentle relaxing chord: C5 - E5 - G5 - C6)
            self._sound_cache["break_start"] = self._generate_sine_chime_wav(
                [523.25, 659.25, 783.99, 1046.50], duration=1.6
            )
            # 2. Focus Start (Fresh uplifting chime: F5 - A5 - C6)
            self._sound_cache["focus_start"] = self._generate_sine_chime_wav(
                [698.46, 880.00, 1046.50], duration=1.3
            )
            # 3. Eye Rest (Soft micro chime: D5 - A5)
            self._sound_cache["eye_rest"] = self._generate_sine_chime_wav(
                [587.33, 880.00], duration=0.8
            )
        except Exception as e:
            print(f"[AudioManager] Failed to synthesize sounds: {e}")

    def play(self, sound_name: str):
        if not self.enabled or not winsound:
            return

        wav_bytes = self._sound_cache.get(sound_name)
        if not wav_bytes:
            return

        def _worker():
            try:
                winsound.PlaySound(
                    wav_bytes,
                    winsound.SND_MEMORY | winsound.SND_ASYNC | winsound.SND_NODEFAULT
                )
            except Exception as e:
                print(f"[AudioManager] Playback error: {e}")

        threading.Thread(target=_worker, daemon=True).start()

    def play_break_chime(self):
        self.play("break_start")

    def play_focus_chime(self):
        self.play("focus_start")

    def play_eye_chime(self):
        self.play("eye_rest")

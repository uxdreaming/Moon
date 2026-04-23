import subprocess
import threading
import time
import numpy as np
import sounddevice as sd
from config import SAMPLE_RATE

SILENCE_THRESHOLD = 0.01
SILENCE_SECONDS = 10.0
SILENCE_SECONDS_SYSTEM = 20 * 60.0
CHUNK_SIZE = 1024


class AudioRecorder:
    def __init__(self):
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def pause(self):
        self._pause_event.set()

    def resume(self):
        self._pause_event.clear()

    def record(self) -> np.ndarray:
        self._stop_event.clear()
        self._pause_event.clear()
        frames = []
        pre_buffer = []
        PRE_BUFFER_CHUNKS = 4
        silent_chunks = 0
        speaking = False
        silence_limit = int(SAMPLE_RATE / CHUNK_SIZE * SILENCE_SECONDS)

        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32", blocksize=CHUNK_SIZE) as stream:
            while not self._stop_event.is_set():
                if self._pause_event.is_set():
                    time.sleep(0.05)
                    continue

                chunk, _ = stream.read(CHUNK_SIZE)
                amplitude = np.abs(chunk).mean()

                if amplitude > SILENCE_THRESHOLD:
                    if not speaking:
                        frames.extend(pre_buffer)
                        pre_buffer = []
                    speaking = True
                    silent_chunks = 0
                    frames.append(chunk.copy())
                elif speaking:
                    frames.append(chunk.copy())
                    silent_chunks += 1
                    if silent_chunks >= silence_limit:
                        break
                else:
                    pre_buffer.append(chunk.copy())
                    if len(pre_buffer) > PRE_BUFFER_CHUNKS:
                        pre_buffer.pop(0)

        if not frames:
            return np.array([], dtype=np.float32)
        return np.concatenate(frames).flatten()

    def record_system(self) -> np.ndarray:
        self._stop_event.clear()
        self._pause_event.clear()
        frames = []
        silent_chunks = 0
        speaking = False
        silence_limit = int(SAMPLE_RATE / CHUNK_SIZE * SILENCE_SECONDS_SYSTEM)
        chunk_bytes = CHUNK_SIZE * 4  # float32le = 4 bytes per sample

        monitor = self._find_monitor_source()
        if not monitor:
            return np.array([], dtype=np.float32)

        proc = subprocess.Popen(
            ['/usr/bin/parec', f'--device={monitor}', '--raw',
             f'--rate={SAMPLE_RATE}', '--channels=1', '--format=float32le'],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )

        try:
            while not self._stop_event.is_set():
                data = proc.stdout.read(chunk_bytes)
                if not data:
                    break
                chunk = np.frombuffer(data, dtype=np.float32)
                amplitude = np.abs(chunk).mean()

                if amplitude > SILENCE_THRESHOLD:
                    speaking = True
                    silent_chunks = 0
                    frames.append(chunk.copy())
                elif speaking:
                    frames.append(chunk.copy())
                    silent_chunks += 1
                    if silent_chunks >= silence_limit:
                        break
        finally:
            proc.terminate()
            proc.wait()

        if not frames:
            return np.array([], dtype=np.float32)
        return np.concatenate(frames).flatten()

    def _find_monitor_source(self):
        result = subprocess.run(
            ['/usr/bin/pactl', 'list', 'sources', 'short'],
            capture_output=True, text=True
        )
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 2 and '.monitor' in parts[1]:
                return parts[1]
        return None

    def is_mic_available(self):
        try:
            result = subprocess.run(
                ['/usr/bin/pactl', 'list', 'sources', 'short'],
                capture_output=True, text=True, timeout=2
            )
            return 'GM300' in result.stdout
        except Exception:
            return False

    def list_devices(self):
        print(sd.query_devices())

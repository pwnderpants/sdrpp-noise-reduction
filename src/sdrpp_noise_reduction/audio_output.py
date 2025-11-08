import queue
import numpy as np
import sounddevice as sd

audio_buffer = np.array([], dtype=np.float32)


def audio_callback(outdata, frames, time_info, status, processed_audio_queue: queue.Queue):
    global audio_buffer

    if status:
        print(f"Audio status: {status}")

    while len(audio_buffer) < frames:
        try:
            audio_chunk = processed_audio_queue.get_nowait()
            audio_buffer = np.concatenate([audio_buffer, audio_chunk])
        except queue.Empty:
            needed = frames - len(audio_buffer)
            audio_buffer = np.concatenate([audio_buffer, np.zeros(needed, dtype=np.float32)])
            break

    if len(audio_buffer) >= frames:
        outdata[:, 0] = audio_buffer[:frames]
        audio_buffer = audio_buffer[frames:]
    else:
        outdata[:, 0] = np.pad(audio_buffer, (0, frames - len(audio_buffer)), mode='constant')
        audio_buffer = np.array([], dtype=np.float32)


def create_audio_stream(processed_audio_queue: queue.Queue, sample_rate: int, channels: int, blocksize: int, latency: str):
    callback = lambda outdata, frames, time_info, status: audio_callback(
        outdata, frames, time_info, status, processed_audio_queue
    )

    stream = sd.OutputStream(
        samplerate=sample_rate,
        channels=channels,
        dtype=np.float32,
        blocksize=blocksize,
        latency=latency,
        callback=callback
    )
    
    return stream

import socket
import queue
import numpy as np

from .constants import BUFFER_SIZE, AUDIO_BUFFER_SIZE, SAMPLE_WIDTH
from .utils import put_with_drop_on_full


def receive_udp_audio(port: int, raw_audio_queue: queue.Queue, running_flag) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', port))
    sock.settimeout(1.0)

    print(f"Listening for audio on UDP port {port}...")

    buffer = b''

    while running_flag():
        try:
            data, _ = sock.recvfrom(BUFFER_SIZE)
            buffer += data

            while len(buffer) >= AUDIO_BUFFER_SIZE * SAMPLE_WIDTH:
                chunk = buffer[:AUDIO_BUFFER_SIZE * SAMPLE_WIDTH]
                buffer = buffer[AUDIO_BUFFER_SIZE * SAMPLE_WIDTH:]

                audio_data = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32768.0

                put_with_drop_on_full(raw_audio_queue, audio_data)

        except socket.timeout:
            continue
        except Exception as e:
            if running_flag():
                print(f"Error receiving UDP data: {e}")

    sock.close()

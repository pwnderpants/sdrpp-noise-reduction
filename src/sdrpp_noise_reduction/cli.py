#!/usr/bin/env python3
import argparse
import signal
import threading
import time
import queue
import sounddevice as sd

from .config import NoiseReductionConfig
from .constants import (
    SAMPLE_RATE, CHANNELS, UDP_PORT, BLOCKSIZE, LATENCY,
    DEFAULT_VOICE_LOW_FREQ, DEFAULT_VOICE_HIGH_FREQ
)
from .udp_receiver import receive_udp_audio
from .audio_processor import process_audio
from .audio_output import create_audio_stream
from .commands import command_input_thread


class RunningFlag:
    def __init__(self):
        self._value = True
        self._lock = threading.Lock()

    def __call__(self):
        with self._lock:
            return self._value

    def set(self, value: bool):
        with self._lock:
            self._value = value


def signal_handler(sig, frame, running_flag: RunningFlag):
    running_flag.set(False)
    print("\nShutting down...")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Process SDR++ audio with configurable noise reduction',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Default settings (95% noise reduction, 80-8000 Hz bandpass)
  sdrpp-noise-reduction

  # Moderate noise reduction (70%)
  sdrpp-noise-reduction --noise-reduction 0.7

  # Narrow voice range (300-3400 Hz for telephony)
  sdrpp-noise-reduction --voice-low 300 --voice-high 3400

  # Disable bandpass filter, use only noise reduction
  sdrpp-noise-reduction --no-bandpass

  # Aggressive settings for heavy white noise
  sdrpp-noise-reduction --noise-reduction 0.98 --spectral-gate -30

  # Boost voice by 6 dB for better clarity
  sdrpp-noise-reduction --voice-gain 6.0
        """
    )

    parser.add_argument(
        '--noise-reduction',
        type=float,
        default=0.95,
        metavar='FLOAT',
        help='Noise reduction strength (0.0-1.0, default: 0.95)'
    )

    parser.add_argument(
        '--voice-low',
        type=float,
        default=DEFAULT_VOICE_LOW_FREQ,
        metavar='HZ',
        help=f'Lower bound for voice frequencies in Hz (default: {DEFAULT_VOICE_LOW_FREQ})'
    )

    parser.add_argument(
        '--voice-high',
        type=float,
        default=DEFAULT_VOICE_HIGH_FREQ,
        metavar='HZ',
        help=f'Upper bound for voice frequencies in Hz (default: {DEFAULT_VOICE_HIGH_FREQ})'
    )

    parser.add_argument(
        '--voice-gain',
        type=float,
        default=0.0,
        metavar='DB',
        help='Voice gain boost in dB (-20 to +20, default: 0.0)'
    )

    parser.add_argument(
        '--spectral-gate',
        type=float,
        default=-35.0,
        metavar='DB',
        help='Spectral gating threshold in dB (default: -35.0)'
    )

    parser.add_argument(
        '--noise-profile-samples',
        type=int,
        default=5,
        metavar='N',
        help='Number of initial audio chunks to use for noise profile (default: 5)'
    )

    parser.add_argument(
        '--stationary-threshold',
        type=float,
        default=2.5,
        metavar='FLOAT',
        help='Stationary noise reduction threshold (default: 2.5)'
    )

    parser.add_argument(
        '--no-bandpass',
        action='store_true',
        help='Disable bandpass filtering (process full frequency range)'
    )

    parser.add_argument(
        '--spectral-gating',
        action='store_true',
        help='Enable spectral gating (default: disabled)'
    )

    parser.add_argument(
        '--no-stationary',
        action='store_true',
        help='Disable stationary noise reduction mode (use non-stationary only)'
    )

    parser.add_argument(
        '--udp-port',
        type=int,
        default=UDP_PORT,
        metavar='PORT',
        help=f'UDP port to listen on (default: {UDP_PORT})'
    )

    args = parser.parse_args()

    if not 0.0 <= args.noise_reduction <= 1.0:
        parser.error("--noise-reduction must be between 0.0 and 1.0")

    if args.voice_low >= args.voice_high:
        parser.error("--voice-low must be less than --voice-high")

    if args.voice_low < 0 or args.voice_high > SAMPLE_RATE / 2:
        parser.error(f"Voice frequencies must be between 0 and {SAMPLE_RATE / 2} Hz (Nyquist frequency)")

    if args.noise_profile_samples < 1:
        parser.error("--noise-profile-samples must be at least 1")

    if not -20.0 <= args.voice_gain <= 20.0:
        parser.error("--voice-gain must be between -20.0 and +20.0 dB")

    return args


def main():
    # Main function to start UDP receiver and audio processor.
    args = parse_arguments()

    running_flag = RunningFlag()

    # Create noise reduction configuration
    config = NoiseReductionConfig(
        prop_decrease=args.noise_reduction,
        voice_low_freq=args.voice_low,
        voice_high_freq=args.voice_high,
        spectral_gate_threshold_db=args.spectral_gate,
        noise_profile_samples=args.noise_profile_samples,
        n_std_thresh_stationary=args.stationary_threshold,
        use_bandpass=not args.no_bandpass,
        use_spectral_gating=args.spectral_gating,
        use_stationary_mode=not args.no_stationary,
        voice_gain_db=args.voice_gain
    )

    signal.signal(signal.SIGINT, lambda s, f: signal_handler(s, f, running_flag))
    signal.signal(signal.SIGTERM, lambda s, f: signal_handler(s, f, running_flag))

    print("SDR++ Noise Reduction Processor")
    print("=" * 40)
    print(f"UDP Port: {args.udp_port}")
    print(f"Sample Rate: {SAMPLE_RATE} Hz")
    print(f"Channels: {CHANNELS}")
    print("=" * 40)

    raw_audio_queue = queue.Queue(maxsize=10)
    processed_audio_queue = queue.Queue(maxsize=20)

    udp_thread = threading.Thread(
        target=receive_udp_audio,
        args=(args.udp_port, raw_audio_queue, running_flag),
        daemon=True
    )
    udp_thread.start()

    # Start audio processing thread
    process_thread = threading.Thread(
        target=process_audio,
        args=(raw_audio_queue, config, processed_audio_queue, running_flag),
        daemon=True
    )
    process_thread.start()

    cmd_thread = threading.Thread(
        target=command_input_thread,
        args=(config, running_flag),
        daemon=True
    )
    cmd_thread.start()

    try:
        device_info = sd.query_devices(kind='output')
        print(f"Output device: {device_info['name']}")
    except Exception as e:
        print(f"Warning: Could not query audio device: {e}")

    print("Starting audio playback...")

    stream = None

    try:
        stream = create_audio_stream(
            processed_audio_queue,
            SAMPLE_RATE,
            CHANNELS,
            BLOCKSIZE,
            LATENCY
        )
        stream.start()

        while running_flag():
            time.sleep(0.1)

    except KeyboardInterrupt:
        running_flag.set(False)
    except Exception as e:
        print(f"Fatal error: {e}")
        running_flag.set(False)
    finally:
        if stream is not None:
            stream.stop()
            stream.close()

    print("Exiting...")


if __name__ == "__main__":
    main()

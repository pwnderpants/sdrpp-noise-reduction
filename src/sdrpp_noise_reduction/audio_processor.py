import queue
import numpy as np
import noisereduce as nr
from scipy import signal as scipy_signal

from .config import NoiseReductionConfig
from .constants import SAMPLE_RATE
from .utils import put_with_drop_on_full, format_config_status

bandpass_filter_coeffs = None
bandpass_filter_cache_key = None
bandpass_filter_state = None

noise_profile_initialized = False
noise_profile = None


def get_bandpass_filter_coeffs(low_freq: float, high_freq: float, sample_rate: int):
    global bandpass_filter_coeffs, bandpass_filter_cache_key, bandpass_filter_state

    cache_key = (low_freq, high_freq, sample_rate)
    if bandpass_filter_cache_key is None or bandpass_filter_cache_key != cache_key:
        bandpass_filter_coeffs = None
        bandpass_filter_state = None
        bandpass_filter_cache_key = cache_key

    if bandpass_filter_coeffs is None:
        nyquist = sample_rate / 2
        low = low_freq / nyquist
        high = high_freq / nyquist

        low = max(0.01, min(low, 0.99))
        high = max(0.01, min(high, 0.99))

        if low >= high:
            return None, None

        b, a = scipy_signal.butter(4, [low, high], btype='band')
        bandpass_filter_coeffs = (b, a)
        bandpass_filter_state = scipy_signal.lfilter_zi(b, a)

    return bandpass_filter_coeffs, bandpass_filter_state


def apply_bandpass_filter(audio: np.ndarray, low_freq: float, high_freq: float, sample_rate: int) -> np.ndarray:
    global bandpass_filter_state

    coeffs, _ = get_bandpass_filter_coeffs(low_freq, high_freq, sample_rate)

    if coeffs is None:
        return audio

    b, a = coeffs

    filtered_audio, bandpass_filter_state = scipy_signal.lfilter(
        b, a, audio, zi=bandpass_filter_state
    )

    return filtered_audio


def apply_spectral_gating(audio: np.ndarray, threshold_db: float = -40.0) -> np.ndarray:
    rms = np.sqrt(np.mean(audio ** 2))
    rms_db = 20 * np.log10(rms + 1e-10)

    if rms_db < threshold_db:
        return audio * 0.1
    
    return audio


def initialize_noise_profile(audio_data: np.ndarray, noise_samples: list, samples_collected: int, samples_needed: int) -> tuple:
    # Collect samples and initialize noise profile when enough samples collected.
    noise_samples.append(audio_data)
    samples_collected += 1

    if samples_collected >= samples_needed:
        combined_noise = np.concatenate(noise_samples)
        print("Noise profile initialized")
        return combined_noise, True, samples_collected
    
    return None, False, samples_collected


def apply_noise_reduction(filtered_audio: np.ndarray, cfg: dict) -> np.ndarray:
    # Apply noise reduction using stationary or non-stationary mode.
    global noise_profile_initialized, noise_profile

    if cfg['use_stationary_mode'] and noise_profile_initialized and len(noise_profile) >= len(filtered_audio):
        return nr.reduce_noise(
            y=filtered_audio,
            y_noise=noise_profile[:len(filtered_audio)],
            sr=SAMPLE_RATE,
            stationary=True,
            prop_decrease=cfg['prop_decrease'],
            n_std_thresh_stationary=cfg['n_std_thresh_stationary']
        )
    else:
        return nr.reduce_noise(
            y=filtered_audio,
            sr=SAMPLE_RATE,
            stationary=False,
            prop_decrease=cfg['prop_decrease']
        )


def apply_audio_effects(audio: np.ndarray, cfg: dict) -> np.ndarray:
    # Apply spectral gating and gain adjustments.
    if cfg['use_spectral_gating']:
        audio = apply_spectral_gating(audio, threshold_db=cfg['spectral_gate_threshold_db'])

    if cfg['voice_gain_db'] != 0.0:
        gain_linear = 10.0 ** (cfg['voice_gain_db'] / 20.0)
        audio = audio * gain_linear

    return audio


def finalize_audio(audio: np.ndarray) -> np.ndarray:
    # Convert to float32 and clip to valid range.
    if audio.dtype != np.float32:
        audio = audio.astype(np.float32)

    return np.clip(audio, -1.0, 1.0)


def process_audio_chunk(audio_data: np.ndarray, cfg: dict, noise_samples: list, samples_collected: int, samples_needed: int) -> tuple:
    # Process a single audio chunk through the noise reduction pipeline.
    global noise_profile_initialized, noise_profile

    if not cfg['noise_reduction_enabled']:
        return finalize_audio(audio_data), samples_collected

    if not noise_profile_initialized:
        new_profile, initialized, samples_collected = initialize_noise_profile(
            audio_data, noise_samples, samples_collected, samples_needed
        )
        if initialized:
            noise_profile = new_profile
            noise_profile_initialized = True

    if cfg['use_bandpass']:
        filtered_audio = apply_bandpass_filter(
            audio_data,
            cfg['voice_low_freq'],
            cfg['voice_high_freq'],
            SAMPLE_RATE
        )
    else:
        filtered_audio = audio_data

    processed_audio = apply_noise_reduction(filtered_audio, cfg)
    processed_audio = apply_audio_effects(processed_audio, cfg)

    return finalize_audio(processed_audio), samples_collected


def process_audio(raw_audio_queue: queue.Queue, config: NoiseReductionConfig, processed_audio_queue: queue.Queue, running_flag) -> None:
    # Main audio processing loop that receives raw audio and outputs processed audio.
    global noise_profile_initialized, noise_profile

    cfg = config.get_all()
    
    print("Starting audio processing...")
    status_lines = format_config_status(cfg).split('\n')
    for line in status_lines[1:-1]:  # Skip header and trailing empty line
        print(line)

    noise_samples = []
    samples_collected = 0
    samples_needed = config.noise_profile_samples

    while running_flag():
        try:
            audio_data = raw_audio_queue.get(timeout=1.0)

            cfg = config.get_all()
            
            processed_audio, samples_collected = process_audio_chunk(
                audio_data, cfg, noise_samples, samples_collected, samples_needed
            )

            put_with_drop_on_full(processed_audio_queue, processed_audio)

        except queue.Empty:
            continue
        except Exception as e:
            if running_flag():
                print(f"Error processing audio: {e}")

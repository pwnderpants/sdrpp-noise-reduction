import threading

from .constants import DEFAULT_VOICE_LOW_FREQ, DEFAULT_VOICE_HIGH_FREQ


class NoiseReductionConfig:
    # Thread-safe configuration for noise reduction parameters.
    def __init__(self, prop_decrease=0.95, voice_low_freq=DEFAULT_VOICE_LOW_FREQ,
                 voice_high_freq=DEFAULT_VOICE_HIGH_FREQ, spectral_gate_threshold_db=-35.0,
                 noise_profile_samples=5, n_std_thresh_stationary=2.5,
                 use_bandpass=True, use_spectral_gating=False, use_stationary_mode=True,
                 voice_gain_db=0.0, noise_reduction_enabled=True):
        self._lock = threading.Lock()
        self._prop_decrease = prop_decrease
        self._voice_low_freq = voice_low_freq
        self._voice_high_freq = voice_high_freq
        self._spectral_gate_threshold_db = spectral_gate_threshold_db
        self._noise_profile_samples = noise_profile_samples
        self._n_std_thresh_stationary = n_std_thresh_stationary
        self._use_bandpass = use_bandpass
        self._use_spectral_gating = use_spectral_gating
        self._use_stationary_mode = use_stationary_mode
        self._voice_gain_db = voice_gain_db
        self._noise_reduction_enabled = noise_reduction_enabled

    @property
    def prop_decrease(self):
        with self._lock:
            return self._prop_decrease

    @prop_decrease.setter
    def prop_decrease(self, value):
        with self._lock:
            self._prop_decrease = max(0.0, min(1.0, value))

    @property
    def voice_low_freq(self):
        with self._lock:
            return self._voice_low_freq

    @voice_low_freq.setter
    def voice_low_freq(self, value):
        with self._lock:
            self._voice_low_freq = value

    @property
    def voice_high_freq(self):
        with self._lock:
            return self._voice_high_freq

    @voice_high_freq.setter
    def voice_high_freq(self, value):
        with self._lock:
            self._voice_high_freq = value

    @property
    def spectral_gate_threshold_db(self):
        with self._lock:
            return self._spectral_gate_threshold_db

    @spectral_gate_threshold_db.setter
    def spectral_gate_threshold_db(self, value):
        with self._lock:
            self._spectral_gate_threshold_db = value

    @property
    def noise_profile_samples(self):
        with self._lock:
            return self._noise_profile_samples

    @noise_profile_samples.setter
    def noise_profile_samples(self, value):
        with self._lock:
            self._noise_profile_samples = max(1, int(value))

    @property
    def n_std_thresh_stationary(self):
        with self._lock:
            return self._n_std_thresh_stationary

    @n_std_thresh_stationary.setter
    def n_std_thresh_stationary(self, value):
        with self._lock:
            self._n_std_thresh_stationary = value

    @property
    def use_bandpass(self):
        with self._lock:
            return self._use_bandpass

    @use_bandpass.setter
    def use_bandpass(self, value):
        with self._lock:
            self._use_bandpass = bool(value)

    @property
    def use_spectral_gating(self):
        with self._lock:
            return self._use_spectral_gating

    @use_spectral_gating.setter
    def use_spectral_gating(self, value):
        with self._lock:
            self._use_spectral_gating = bool(value)

    @property
    def use_stationary_mode(self):
        with self._lock:
            return self._use_stationary_mode

    @use_stationary_mode.setter
    def use_stationary_mode(self, value):
        with self._lock:
            self._use_stationary_mode = bool(value)

    @property
    def voice_gain_db(self):
        with self._lock:
            return self._voice_gain_db

    @voice_gain_db.setter
    def voice_gain_db(self, value):
        with self._lock:
            self._voice_gain_db = max(-20.0, min(20.0, value))

    @property
    def noise_reduction_enabled(self):
        with self._lock:
            return self._noise_reduction_enabled

    @noise_reduction_enabled.setter
    def noise_reduction_enabled(self, value):
        with self._lock:
            self._noise_reduction_enabled = bool(value)

    def get_all(self):
        with self._lock:
            return {
                'prop_decrease': self._prop_decrease,
                'voice_low_freq': self._voice_low_freq,
                'voice_high_freq': self._voice_high_freq,
                'spectral_gate_threshold_db': self._spectral_gate_threshold_db,
                'noise_profile_samples': self._noise_profile_samples,
                'n_std_thresh_stationary': self._n_std_thresh_stationary,
                'use_bandpass': self._use_bandpass,
                'use_spectral_gating': self._use_spectral_gating,
                'use_stationary_mode': self._use_stationary_mode,
                'voice_gain_db': self._voice_gain_db,
                'noise_reduction_enabled': self._noise_reduction_enabled
            }

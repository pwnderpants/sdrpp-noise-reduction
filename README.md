# SDR++ Noise Reduction

Processes network radio audio from SDR++ via UDP, applies configurable noise reduction, and outputs to the default audio sink.

## Features

- Real-time noise reduction using spectral subtraction
- Configurable voice frequency bandpass filtering
- Stationary and non-stationary noise reduction modes
- Spectral gating for additional noise suppression
- Voice gain boost
- Interactive command interface for runtime adjustments
- Thread-safe configuration

## Installation

### From Source

```bash
git clone <repository-url>
cd sdrpp-noise-reduction
pip install -e .
```

### Dependencies

- Python 3.8+
- numpy >= 1.21.0
- sounddevice >= 0.4.6
- noisereduce >= 2.0.0
- scipy >= 1.7.0

Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
sdrpp-noise-reduction
```

### Command Line Options

```bash
sdrpp-noise-reduction --help
```

Common options:
- `--noise-reduction <0.0-1.0>` - Noise reduction strength (default: 0.95)
- `--voice-low <Hz>` - Lower voice frequency bound (default: 80)
- `--voice-high <Hz>` - Upper voice frequency bound (default: 8000)
- `--voice-gain <dB>` - Voice gain boost -20 to +20 dB (default: 0.0)
- `--spectral-gate <dB>` - Spectral gating threshold in dB (default: -35.0)
- `--noise-profile-samples <N>` - Number of initial audio chunks for noise profile (default: 5)
- `--stationary-threshold <FLOAT>` - Stationary noise reduction threshold (default: 2.5)
- `--udp-port <PORT>` - UDP port to listen on (default: 7355)
- `--no-bandpass` - Disable bandpass filtering
- `--spectral-gating` - Enable spectral gating (default: disabled)
- `--no-stationary` - Disable stationary noise reduction mode

### Examples

```bash
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
```

### Interactive Commands

While running, you can use interactive commands:

- `/noise_reduction <0.0-1.0>` or `/nr` - Set noise reduction strength
- `/voice_low <Hz>` or `/vl` - Set lower voice frequency bound
- `/voice_high <Hz>` or `/vh` - Set upper voice frequency bound
- `/voice_gain <dB>` or `/vg` - Set voice gain boost (-20 to +20 dB)
- `/spectral_gate <dB>` or `/sg` - Set spectral gating threshold
- `/stationary_threshold <val>` or `/st` - Set stationary noise threshold
- `/bandpass <on|off>` or `/bp` - Enable/disable bandpass filter
- `/spectral_gating <on|off>` or `/spg` - Enable/disable spectral gating
- `/stationary <on|off>` or `/stat` - Enable/disable stationary mode
- `/noise <on|off>` - Enable/disable noise reduction
- `/status` or `/s` - Show current settings
- `/help` or `/h` - Show help
- `/quit`, `/exit`, or `/q` - Exit the program

## Configuration

### SDR++ Setup

The application receives audio from SDR++ via UDP. Follow these steps to configure SDR++ to send audio over the network:

1. **Open SDR++ Settings**
   - Launch SDR++ and go to `Settings` → `Audio`

2. **Configure Audio Output**
   - Set the **Output** dropdown to `Network (UDP)`
   - In the **Network** section, configure:
     - **Host**: Enter the IP address of the machine running this application
       - For localhost (same machine): `127.0.0.1` or `localhost`
       - For remote machine: Use the machine's IP address (e.g., `192.168.1.100`)
     - **Port**: `7355` (default) or match the port specified with `--udp-port`
     - **Sample Rate**: `48000` Hz (required)
     - **Channels**: `Mono` (1 channel)

3. **Audio Format Settings**
   - Ensure the audio format is set to **16-bit PCM**
   - The application expects raw PCM audio data (not encoded formats)

4. **Apply Settings**
   - Click `Apply` or `OK` to save the settings
   - Start receiving audio in SDR++ (tune to a frequency)

5. **Verify Connection**
   - Start this application: `sdrpp-noise-reduction`
   - You should see: `Listening for audio on UDP port 7355...`
   - If audio is being received, the application will process and output it to your default audio device

**Note**: If running SDR++ and this application on different machines, ensure:
- Both machines are on the same network (or configure firewall rules)
- The UDP port (default 7355) is not blocked by a firewall
- The IP address is correct and reachable

**Troubleshooting**:
- If no audio is received, check that SDR++ is actually receiving/playing audio
- Verify the UDP port matches between SDR++ and this application
- Check firewall settings if using a remote connection
- Ensure SDR++ sample rate is set to 48000 Hz

## Project Structure

```
sdrpp-noise-reduction/
├── src/
│   └── sdrpp_noise_reduction/
│       ├── __init__.py
│       ├── constants.py          # Constants (sample rate, etc.)
│       ├── config.py             # NoiseReductionConfig class
│       ├── udp_receiver.py        # UDP audio receiver
│       ├── audio_processor.py     # Audio processing logic
│       ├── audio_output.py        # Audio output/callback
│       ├── commands.py            # Interactive command handling
│       ├── cli.py                 # CLI argument parsing & main
│       └── utils.py               # Utility functions (queue helpers, formatting)
├── tests/                         # Unit tests
├── pyproject.toml                 # Package configuration
├── requirements.txt               # Dependencies
└── README.md                      # This file
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

Follow PEP 8 style guidelines.

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

from .config import NoiseReductionConfig
from .constants import SAMPLE_RATE
from .utils import format_config_status


def print_help():
    print("\nAvailable commands:")
    print("  /noise_reduction <0.0-1.0>  - Set noise reduction strength (e.g., 0.95 = 95%)")
    print("  /voice_low <Hz>              - Set lower voice frequency bound")
    print("  /voice_high <Hz>            - Set upper voice frequency bound")
    print("  /voice_gain <dB>            - Set voice gain boost (-20 to +20 dB)")
    print("  /spectral_gate <dB>         - Set spectral gating threshold")
    print("  /stationary_threshold <val> - Set stationary noise threshold")
    print("  /bandpass <on|off>          - Enable/disable bandpass filter")
    print("  /spectral_gating <on|off>   - Enable/disable spectral gating")
    print("  /stationary <on|off>        - Enable/disable stationary mode")
    print("  /noise <on|off>             - Enable/disable noise reduction")
    print("  /status                     - Show current settings")
    print("  /help                       - Show this help")
    print("  /quit                       - Exit the program")
    print()


def handle_numeric_command(parts: list, usage: str, validator, setter, success_msg: str, error_msg: str = None) -> bool:
    # Handle numeric command with validation. Returns True to continue.
    if len(parts) < 2:
        print(f"Usage: {usage}")
        return True
    
    try:
        value = float(parts[1])
        if validator(value):
            setter(value)
            print(success_msg.format(value))
        elif error_msg:
            print(error_msg)
    except ValueError:
        print("Error: Invalid number")
    
    return True


def handle_toggle_command(parts: list, usage: str, setter, enabled_msg: str, disabled_msg: str) -> bool:
    # Handle on/off toggle command. Returns True to continue.
    if len(parts) < 2:
        print(f"Usage: {usage}")
        return True
    
    value = parts[1].lower()
    if value in ('on', '1', 'true', 'enable'):
        setter(True)
        print(enabled_msg)
    elif value in ('off', '0', 'false', 'disable'):
        setter(False)
        print(disabled_msg)
    else:
        print(f"Usage: {usage}")
    
    return True


def handle_command(cmd: str, config: NoiseReductionConfig) -> bool:
    # Handle interactive command. Returns True if should continue, False if should quit.
    parts = cmd.strip().split()
    if not parts:
        return True

    command = parts[0].lower()

    if command in ('/quit', '/exit', '/q'):
        return False

    elif command in ('/help', '/h'):
        print_help()
        return True

    elif command in ('/status', '/s'):
        cfg = config.get_all()
        print(format_config_status(cfg))
        return True

    elif command in ('/noise_reduction', '/nr'):
        return handle_numeric_command(
            parts,
            "/noise_reduction <0.0-1.0>",
            lambda v: 0.0 <= v <= 1.0,
            lambda v: setattr(config, 'prop_decrease', v),
            "Noise reduction set to {:.1f}%",
            "Error: Noise reduction must be between 0.0 and 1.0"
        )

    elif command in ('/voice_low', '/vl'):
        return handle_numeric_command(
            parts,
            "/voice_low <Hz>",
            lambda v: 0 <= v < config.voice_high_freq,
            lambda v: setattr(config, 'voice_low_freq', v),
            "Voice low frequency set to {} Hz",
            f"Error: Must be between 0 and {config.voice_high_freq} Hz"
        )

    elif command in ('/voice_high', '/vh'):
        return handle_numeric_command(
            parts,
            "/voice_high <Hz>",
            lambda v: v > config.voice_low_freq and v <= SAMPLE_RATE / 2,
            lambda v: setattr(config, 'voice_high_freq', v),
            "Voice high frequency set to {} Hz",
            f"Error: Must be between {config.voice_low_freq} and {SAMPLE_RATE / 2} Hz"
        )

    elif command in ('/voice_gain', '/vg'):
        return handle_numeric_command(
            parts,
            "/voice_gain <dB> (range: -20 to +20)",
            lambda v: -20.0 <= v <= 20.0,
            lambda v: setattr(config, 'voice_gain_db', v),
            "Voice gain set to {:+.1f} dB",
            "Error: Voice gain must be between -20 and +20 dB"
        )

    elif command in ('/spectral_gate', '/sg'):
        return handle_numeric_command(
            parts,
            "/spectral_gate <dB>",
            lambda v: True,
            lambda v: setattr(config, 'spectral_gate_threshold_db', v),
            "Spectral gate threshold set to {} dB"
        )

    elif command in ('/stationary_threshold', '/st'):
        return handle_numeric_command(
            parts,
            "/stationary_threshold <value>",
            lambda v: True,
            lambda v: setattr(config, 'n_std_thresh_stationary', v),
            "Stationary threshold set to {}"
        )

    elif command in ('/bandpass', '/bp'):
        return handle_toggle_command(
            parts,
            "/bandpass <on|off>",
            lambda v: setattr(config, 'use_bandpass', v),
            "Bandpass filter enabled",
            "Bandpass filter disabled"
        )

    elif command in ('/spectral_gating', '/spg'):
        return handle_toggle_command(
            parts,
            "/spectral_gating <on|off>",
            lambda v: setattr(config, 'use_spectral_gating', v),
            "Spectral gating enabled",
            "Spectral gating disabled"
        )

    elif command in ('/stationary', '/stat'):
        return handle_toggle_command(
            parts,
            "/stationary <on|off>",
            lambda v: setattr(config, 'use_stationary_mode', v),
            "Stationary mode enabled",
            "Stationary mode disabled"
        )

    elif command == '/noise':
        return handle_toggle_command(
            parts,
            "/noise <on|off>",
            lambda v: setattr(config, 'noise_reduction_enabled', v),
            "Noise reduction enabled",
            "Noise reduction disabled"
        )

    else:
        print(f"Unknown command: {command}. Type /help for available commands.")
        return True


def command_input_thread(config: NoiseReductionConfig, running_flag):
    print("\nInteractive command prompt ready. Type /help for commands.\n")

    while running_flag():
        try:
            try:
                cmd = input()
            except EOFError:
                break
            except KeyboardInterrupt:
                running_flag.set(False)
                break

            if cmd.strip():
                if not handle_command(cmd, config):
                    running_flag.set(False)
                    break

        except KeyboardInterrupt:
            running_flag.set(False)
            break
        except Exception as e:
            if running_flag():
                print(f"Error processing command: {e}")

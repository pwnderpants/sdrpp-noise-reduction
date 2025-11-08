import queue


def put_with_drop_on_full(q: queue.Queue, item, timeout: float = 0.1):
    # Put item in queue, dropping oldest item if queue is full.
    try:
        q.put(item, timeout=timeout)
    except queue.Full:
        try:
            q.get_nowait()
            q.put(item, timeout=timeout)
        except queue.Empty:
            pass


def format_config_status(cfg: dict) -> str:
    # Format configuration status as a string for display.
    lines = ["\nCurrent settings:"]
    
    if not cfg['noise_reduction_enabled']:
        lines.append("  Noise reduction: DISABLED")
    else:
        lines.append(f"  Noise reduction: {cfg['prop_decrease']*100:.1f}%")
        lines.append(f"  Voice frequency range: {cfg['voice_low_freq']}-{cfg['voice_high_freq']} Hz")
        lines.append(f"  Voice gain: {cfg['voice_gain_db']:+.1f} dB")
        lines.append(f"  Spectral gate threshold: {cfg['spectral_gate_threshold_db']:.1f} dB")
        lines.append(f"  Stationary threshold: {cfg['n_std_thresh_stationary']:.2f}")
        lines.append(f"  Bandpass filter: {'enabled' if cfg['use_bandpass'] else 'disabled'}")
        lines.append(f"  Spectral gating: {'enabled' if cfg['use_spectral_gating'] else 'disabled'}")
        lines.append(f"  Stationary mode: {'enabled' if cfg['use_stationary_mode'] else 'disabled'}")
    
    lines.append("")
    return "\n".join(lines)

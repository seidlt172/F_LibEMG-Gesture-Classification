"""
mindrove_streamer.py
====================
MindRove Armband -> UDP bridge for LibEMG.

This script connects to the MindRove armband over WiFi and forwards
raw EMG samples over UDP (localhost:12345) in the format that
LibEMG's OnlineDataHandler expects (pickled list of 8 values per sample).

Run this FIRST, in a separate terminal, before any LibEMG script.

Usage:
    python scripts/mindrove_streamer.py

Requirements:
    pip install mindrove

Hardware:
    1. Power on the MindRove armband.
    2. Connect your PC to the armband's WiFi network (SSID: MindRove_XXXX).
    3. Then run this script.

What it does:
    - Connects to armband at 192.168.4.1:4210 (default MindRove WiFi address)
    - Polls the internal ring buffer every ~10 ms
    - Pickles each new sample row and sends it over UDP to localhost:12345
    - LibEMG's OnlineDataHandler listens on that port

Press Ctrl+C to stop cleanly.
"""

import pickle
import socket
import time

import mindrove
from mindrove.board_shim import (
    BoardIds,
    BoardShim,
    IpProtocolTypes,
    MindRoveError,
    MindRoveInputParams,
)

# ── Hardware connection settings (do not change unless your armband differs) ──
MINDROVE_IP = "192.168.4.1"
MINDROVE_PORT = 4210

# ── UDP output settings (must match OnlineDataHandler in LibEMG scripts) ──
UDP_HOST = "127.0.0.1"
UDP_PORT = 12345

# ── Poll interval (seconds) ──
POLL_INTERVAL = 0.010  # 10 ms → ~100 polls/sec, well above 500 Hz sample rate

# ── Battery UDP output (separate port so EMG stream is unchanged) ──
BATTERY_UDP_PORT    = 12346
BATTERY_REPORT_SECS = 5.0   # send battery level every 5 seconds


def build_board():
    params = MindRoveInputParams()
    params.ip_address = MINDROVE_IP
    params.ip_port = MINDROVE_PORT
    params.ip_protocol = IpProtocolTypes.UDP.value

    board_id = BoardIds.MINDROVE_WIFI_BOARD.value
    board = BoardShim(board_id, params)
    return board, board_id


def main():
    print("=" * 55)
    print("  MindRove -> LibEMG UDP Streamer")
    print("=" * 55)
    print(f"  Armband target : {MINDROVE_IP}:{MINDROVE_PORT} (UDP)")
    print(f"  UDP output     : {UDP_HOST}:{UDP_PORT}")
    print(f"  Poll interval  : {POLL_INTERVAL * 1000:.0f} ms")
    print()

    BoardShim.enable_dev_board_logger()

    board = None
    sock         = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    battery_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        print("[1/3] Creating board connection...")
        board, board_id = build_board()

        print("[2/3] Preparing session (connecting to armband)...")
        board.prepare_session()
        print("      Session prepared OK.")

        print("[3/3] Starting data stream...")
        board.start_stream(450000)  # 450 000-sample ring buffer
        print("      Stream started OK.")

        # Switch to measurement mode (same call used in your probe/live-check scripts)
        try:
            board.config_board(mindrove.MindroveConfigMode.EEG_MODE)
            print("      Board configured to measurement mode.")
        except Exception as e:
            print(f"      [WARN] config_board ignored: {e}")

        # Discover channel layout
        fs = BoardShim.get_sampling_rate(board_id)
        emg_channels = BoardShim.get_emg_channels(board_id)
        if not emg_channels:
            # Fallback: use all EXG channels if EMG-specific list is empty
            emg_channels = BoardShim.get_exg_channels(board_id)

        print()
        print(f"  Sampling rate : {fs} Hz")
        print(f"  EMG channels  : {emg_channels}  ({len(emg_channels)} ch)")

        # Battery channel (may be empty on some firmware versions)
        try:
            battery_channels = BoardShim.get_battery_channel(board_id)
            battery_ch = battery_channels if isinstance(battery_channels, int) else battery_channels[0]
            print(f"  Battery ch    : {battery_ch}")
        except Exception:
            battery_ch = None
            print("  Battery ch    : not available")

        print()
        print("  Streaming to LibEMG... (Ctrl+C to stop)")
        print("-" * 55)

        packets_sent      = 0
        samples_sent      = 0
        last_battery_time = 0.0
        report_every      = 200

        while True:
            count = board.get_board_data_count()
            if count <= 0:
                time.sleep(POLL_INTERVAL)
                continue

            data = board.get_board_data(count)   # shape: (n_channels, n_samples)
            n_samples = data.shape[1]
            if n_samples == 0:
                time.sleep(POLL_INTERVAL)
                continue

            # Send one UDP datagram per sample so LibEMG gets one row at a time.
            # LibEMG's OnlineDataHandler expects: pickle.loads(packet) -> list of floats
            for s in range(n_samples):
                sample = [float(data[ch, s]) for ch in emg_channels]
                payload = pickle.dumps(sample)
                sock.sendto(payload, (UDP_HOST, UDP_PORT))

            packets_sent += 1
            samples_sent += n_samples

            # ── Battery reporting (every BATTERY_REPORT_SECS seconds) ──
            now = time.time()
            if battery_ch is not None and (now - last_battery_time) >= BATTERY_REPORT_SECS:
                try:
                    batt_data = board.get_current_board_data(1)
                    batt_val  = float(batt_data[battery_ch, -1])
                    payload   = pickle.dumps({'type': 'battery', 'value': batt_val})
                    battery_sock.sendto(payload, (UDP_HOST, BATTERY_UDP_PORT))
                    last_battery_time = now
                except Exception:
                    pass

            if packets_sent % report_every == 0:
                print(
                    f"  pkt={packets_sent:6d} | "
                    f"samples_sent={samples_sent:8d} | "
                    f"last_batch={n_samples:4d}"
                )

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\n[Stopped by user]")

    except MindRoveError as e:
        print(f"\n[ERROR] MindRoveError: {e}")
        raise

    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}")
        raise

    finally:
        print("Cleaning up...")
        sock.close()
        battery_sock.close()
        if board is not None:
            try:
                if board.is_prepared():
                    board.release_session()
                    print("Session released.")
            except Exception as e:
                print(f"[WARN] release_session failed: {e}")
        print("Done.")


if __name__ == "__main__":
    main()
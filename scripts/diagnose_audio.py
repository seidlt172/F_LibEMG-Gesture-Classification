"""
diagnose_audio.py
=================
Diagnostiziert verfügbare Audio-Geräte und testet Stream-Opening.
"""

import pyaudio
import time

print("\n" + "="*60)
print("AUDIO DEVICE DIAGNOSTIK")
print("="*60 + "\n")

try:
    p = pyaudio.PyAudio()
    print(f"✓ PyAudio initialisiert ({p.get_device_count()} Geräte gefunden)\n")
    
    print("VERFÜGBARE INPUT-GERÄTE:")
    print("-" * 60)
    
    input_devices = []
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:
            input_devices.append(i)
            default = " [DEFAULT]" if i == p.get_default_input_device_info()['index'] else ""
            print(f"[{i}] {info['name']}")
            print(f"    Kanäle: {info['maxInputChannels']}, Sample Rate: {int(info['defaultSampleRate'])} Hz{default}\n")
    
    if not input_devices:
        print("✗ KEINE INPUT-GERÄTE GEFUNDEN!")
        p.terminate()
        exit(1)
    
    print("\nTESTE STREAM-OPENING AUF JEDEM GERÄT:")
    print("-" * 60)
    
    for device_id in input_devices:
        info = p.get_device_info_by_index(device_id)
        print(f"\n[{device_id}] {info['name']}...", end=" ", flush=True)
        
        start_time = time.time()
        try:
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=44100,
                input=True,
                input_device_index=device_id,
                frames_per_buffer=1024,
            )
            elapsed = time.time() - start_time
            stream.close()
            print(f"✓ OK ({elapsed:.2f}s)")
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"✗ FEHLER ({elapsed:.2f}s): {e}")
    
    print("\n" + "="*60)
    print("EMPFEHLUNG:")
    print("="*60)
    if len(input_devices) > 1:
        print(f"✓ Mehrere Mikrofone gefunden. Das erste funktionsfähige wird automatisch verwendet.")
    elif len(input_devices) == 1:
        print(f"✓ Nur 1 Mikrofon gefunden: Gerät {input_devices[0]}")
    
    p.terminate()
    
except Exception as e:
    print(f"✗ FEHLER: {e}")
    import traceback
    traceback.print_exc()

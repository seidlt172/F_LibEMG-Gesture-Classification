import threading
import wave
import logging
import os
import pyaudio

logger = logging.getLogger(__name__)


class AudioRecorder:
    def __init__(self,
                 output_filename: str = "temp_voice.wav",
                 channels: int = 1,
                 rate: int = 44100,
                 chunk: int = 1024,
                 format=pyaudio.paInt16):
        self.output_filename = output_filename
        self.channels = channels
        self.rate = rate
        self.chunk = chunk
        self.format = format

        logger.info("Initializing PyAudio...")
        self._audio = pyaudio.PyAudio()
        logger.info("✓ PyAudio initialized")
        
        self._stream = None
        self._frames = []
        self._thread = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._recording_flag = False

    @property
    def is_recording(self) -> bool:
        """Simple check if recording flag is set."""
        with self._lock:
            return self._recording_flag

    def start_recording(self) -> None:
        """Start recording using the system default microphone."""
        with self._lock:
            if self._recording_flag:
                raise RuntimeError("Recording already running")
            self._recording_flag = True
            self._frames = []
            self._stop_event.clear()

        # Open stream OUTSIDE the lock
        logger.info("Opening stream on system default microphone...")
        try:
            self._stream = self._audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk,
            )
            logger.info("✓ Stream opened successfully")
        except Exception as e:
            with self._lock:
                self._recording_flag = False
            logger.error(f"Stream open failed: {e}", exc_info=True)
            raise
        
        # Start recording thread
        self._thread = threading.Thread(target=self._record_loop, daemon=True)
        self._thread.start()
        logger.info("✓ Recording thread started")

    def _record_loop(self) -> None:
        """Record audio frames in loop."""
        try:
            logger.info("Recording loop: ACTIVE")
            frame_count = 0
            while not self._stop_event.is_set():
                data = self._stream.read(self.chunk, exception_on_overflow=False)
                with self._lock:
                    self._frames.append(data)
                frame_count += 1
                if frame_count % 50 == 0:  # Log every 50 frames (~1 sec)
                    logger.debug(f"Recording: {frame_count} frames captured")
            logger.info(f"Recording loop: STOPPED ({frame_count} total frames)")
        except Exception as exc:
            logger.error(f"Record loop error: {exc}", exc_info=True)
        finally:
            if self._stream:
                try:
                    self._stream.stop_stream()
                    self._stream.close()
                except:
                    pass
                self._stream = None

    def stop_recording(self) -> None:
        """Stop recording and save WAV."""
        logger.info("Stopping recording...")
        
        with self._lock:
            if not self._recording_flag:
                logger.warning("Not recording")
                return
            self._stop_event.set()
            self._recording_flag = False
        
        # Wait for thread
        if self._thread:
            self._thread.join(timeout=3.0)
            self._thread = None
        
        # Save file
        self._write_wav()
        logger.info("✓ Recording stopped and saved")

    def _write_wav(self) -> None:
        """Write frames to WAV file."""
        with self._lock:
            frames = list(self._frames)
        
        logger.info(f"Writing {len(frames)} frames to {self.output_filename}...")
        
        if not frames:
            logger.error("ERROR: No audio frames captured!")
            return
        
        try:
            with wave.open(self.output_filename, "wb") as f:
                f.setnchannels(self.channels)
                f.setsampwidth(self._audio.get_sample_size(self.format))
                f.setframerate(self.rate)
                f.writeframes(b"".join(frames))
            
            # Verify file
            if os.path.exists(self.output_filename):
                file_size = os.path.getsize(self.output_filename)
                logger.info(f"✓ WAV saved: {self.output_filename}")
                logger.info(f"✓ File size: {file_size} bytes ({len(frames)} frames)")
                if file_size < 100:
                    logger.error(f"ERROR: WAV file too small ({file_size} bytes) - possible recording failure")
            else:
                logger.error(f"ERROR: File was not created: {self.output_filename}")
        except Exception as exc:
            logger.error(f"Failed to write WAV file: {exc}", exc_info=True)
            raise

    def close(self) -> None:
        """Cleanup."""
        if self.is_recording:
            self.stop_recording()
        
        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except:
                pass
        
        try:
            self._audio.terminate()
            logger.info("✓ PyAudio closed")
        except Exception as exc:
            logger.error(f"Close error: {exc}", exc_info=True)

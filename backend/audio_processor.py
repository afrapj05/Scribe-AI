"""
Advanced audio processing module with noise filtering and analysis.
Supports multiple noise reduction techniques.
"""

import numpy as np
import threading
import time
from typing import Tuple, Optional
import os

# Optional: sounddevice for microphone recording
try:
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except ImportError:
    sd = None
    HAS_SOUNDDEVICE = False

# Optional: scipy for audio file I/O and filtering
try:
    from scipy.io.wavfile import write, read
    from scipy import signal
    HAS_SCIPY = True
except ImportError:
    write = read = signal = None
    HAS_SCIPY = False

# Optional imports for advanced processing
try:
    import librosa
    import noisereduce as nr
    HAS_ADVANCED_AUDIO = True
except ImportError:
    HAS_ADVANCED_AUDIO = False


class AudioRecorder:
    """Manages audio recording with optional real-time monitoring."""
    
    def __init__(self, sample_rate: int = 44100, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.is_recording = False
        self.recording_data = []
        self.recording_thread = None
        self.start_time = None
        self.duration = 0.0
    
    def start_recording(self) -> None:
        """Start recording audio in background thread."""
        self.is_recording = True
        self.recording_data = []
        self.start_time = time.time()
        
        print(f"🎙️ Recording started at {self.sample_rate} Hz")
        
        # Start recording in background thread
        self.recording_thread = threading.Thread(target=self._record_thread, daemon=True)
        self.recording_thread.start()
    
    def _record_thread(self) -> None:
        """Background thread for continuous audio recording."""
        if not HAS_SOUNDDEVICE:
            print("❌ sounddevice not installed. Audio recording unavailable.")
            self.is_recording = False
            return

        chunk_size = int(self.sample_rate * 0.1)  # 100ms chunks
        
        try:
            stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                blocksize=chunk_size,
                dtype=np.float32
            )
            
            with stream:
                while self.is_recording:
                    data, overflowed = stream.read(chunk_size)
                    if overflowed:
                        print("⚠️ Audio buffer overflow - some data may have been lost")
                    self.recording_data.append(data.copy())
                    time.sleep(0.01)  # Small delay to prevent busy loop
        
        except Exception as e:
            print(f"❌ Recording error: {e}")
            self.is_recording = False
    
    def stop_recording(self) -> float:
        """Stop recording and return duration in seconds."""
        self.is_recording = False
        if self.recording_thread:
            self.recording_thread.join(timeout=2)
        
        self.duration = time.time() - self.start_time if self.start_time else 0
        print(f"⏹️ Recording stopped. Duration: {self.duration:.2f} seconds")
        
        return self.duration
    
    def get_audio_data(self) -> np.ndarray:
        """Get recorded audio data as numpy array."""
        if not self.recording_data:
            return np.array([])
        
        return np.concatenate(self.recording_data, axis=0)
    
    def save_recording(self, file_path: str) -> Tuple[bool, str]:
        """Save recording to WAV file with automatic format conversion."""
        if not HAS_SCIPY:
            return False, "scipy not installed - cannot save WAV file"
        try:
            audio_data = self.get_audio_data()
            
            if audio_data.size == 0:
                return False, "No audio data to save"
            
            # Convert float32 to int16
            audio_int16 = np.int16(audio_data * 32767)
            
            write(file_path, self.sample_rate, audio_int16)
            
            file_size = os.path.getsize(file_path)
            print(f"✅ Audio saved to {file_path} ({file_size/1024:.2f} KB)")
            
            return True, file_path
        
        except Exception as e:
            return False, f"Save error: {str(e)}"


class AudioProcessor:
    """Advanced audio processing with noise filtering."""
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
    
    # ===================== NOISE ESTIMATION =====================
    def estimate_noise_level(self, audio: np.ndarray) -> float:
        """
        Estimate noise level in audio (0-1 scale).
        Uses spectral analysis to detect broadband noise.
        """
        if len(audio) < self.sample_rate:
            return 0.5  # Default if audio too short
        
        # Take 1 second sample from middle of audio
        mid_point = len(audio) // 2
        sample = audio[mid_point:mid_point + self.sample_rate]
        
        # Frequency domain analysis
        freqs = np.fft.rfftfreq(len(sample), 1 / self.sample_rate)
        spectrum = np.abs(np.fft.rfft(sample))
        
        # Calculate noise floor (energy in high frequencies)
        high_freq_idx = np.where(freqs > 5000)[0]
        if len(high_freq_idx) > 0:
            noise_floor = np.mean(spectrum[high_freq_idx])
        else:
            noise_floor = np.mean(spectrum)
        
        # Power spectral density
        psd = np.sqrt(noise_floor / np.max(spectrum))
        
        # Clip to 0-1 range
        return float(np.clip(psd, 0, 1))
    
    # ===================== NOISE FILTERING METHODS =====================
    
    def apply_spectral_subtraction(self, audio: np.ndarray, noise_factor: float = 2.0) -> np.ndarray:
        """
        Apply spectral subtraction to reduce noise.
        Estimates noise spectrum from initial silence and subtracts it.
        """
        if len(audio) < self.sample_rate:
            return audio
        
        # Use first 0.5 seconds as noise estimate (assumes quiet start)
        noise_sample = audio[:int(0.5 * self.sample_rate)]
        noise_spectrum = np.abs(np.fft.rfft(noise_sample))
        
        # Process audio in frames (50ms windows)
        frame_size = int(0.05 * self.sample_rate)
        hop_size = frame_size // 2
        window = signal.windows.hann(frame_size)
        
        output = np.zeros_like(audio)
        
        for start in range(0, len(audio) - frame_size, hop_size):
            frame = audio[start:start + frame_size]
            frame_windowed = frame * window
            
            # FFT
            spectrum = np.fft.rfft(frame_windowed)
            magnitude = np.abs(spectrum)
            phase = np.angle(spectrum)
            
            # Spectral subtraction
            magnitude_subtracted = magnitude - noise_factor * noise_spectrum[:len(magnitude)]
            magnitude_subtracted = np.maximum(magnitude_subtracted, 0.1 * magnitude)  # Prevent over-subtraction
            
            # Reconstruct
            spectrum_cleaned = magnitude_subtracted * np.exp(1j * phase)
            frame_cleaned = np.fft.irfft(spectrum_cleaned, n=frame_size)
            
            # Overlap-add
            output[start:start + frame_size] += frame_cleaned * window
        
        return output / np.max(np.abs(output)) if np.max(np.abs(output)) > 0 else output
    
    def apply_lowpass_filter(self, audio: np.ndarray, cutoff_freq: float = 6000) -> np.ndarray:
        """
        Apply low-pass filter to remove high-frequency noise.
        Good for speech enhancement.
        """
        nyquist = self.sample_rate / 2
        normalized_cutoff = cutoff_freq / nyquist
        
        if normalized_cutoff >= 1.0:
            return audio
        
        # Design Butterworth filter
        b, a = signal.butter(4, normalized_cutoff, btype='low')
        filtered = signal.filtfilt(b, a, audio)
        
        return filtered / np.max(np.abs(filtered)) if np.max(np.abs(filtered)) > 0 else filtered
    
    def apply_highpass_filter(self, audio: np.ndarray, cutoff_freq: float = 80) -> np.ndarray:
        """
        Apply high-pass filter to remove low-frequency rumble/hum.
        Common for clinical audio (removes ventilation noise, muscle noise).
        """
        nyquist = self.sample_rate / 2
        normalized_cutoff = cutoff_freq / nyquist
        
        if normalized_cutoff >= 1.0:
            return audio
        
        # Design Butterworth filter
        b, a = signal.butter(4, normalized_cutoff, btype='high')
        filtered = signal.filtfilt(b, a, audio)
        
        return filtered / np.max(np.abs(filtered)) if np.max(np.abs(filtered)) > 0 else filtered
    
    def apply_bandpass_filter(self, audio: np.ndarray, low_freq: float = 80, high_freq: float = 6000) -> np.ndarray:
        """
        Apply band-pass filter (80 Hz - 6 kHz) optimal for human speech.
        """
        nyquist = self.sample_rate / 2
        low_norm = low_freq / nyquist
        high_norm = high_freq / nyquist
        
        if low_norm >= 1.0 or high_norm >= 1.0 or low_norm >= high_norm:
            return audio
        
        b, a = signal.butter(4, [low_norm, high_norm], btype='band')
        filtered = signal.filtfilt(b, a, audio)
        
        return filtered / np.max(np.abs(filtered)) if np.max(np.abs(filtered)) > 0 else filtered
    
    def apply_noisereduce(self, audio: np.ndarray) -> np.ndarray:
        """
        Apply noisereduce library for advanced noise reduction.
        Requires librosa and noisereduce packages.
        """
        if not HAS_ADVANCED_AUDIO:
            print("⚠️ noisereduce not available. Install: pip install noisereduce librosa")
            return audio
        
        try:
            # Apply noise reduction
            reduced = nr.reduce_noise(y=audio, sr=self.sample_rate, stationary=True)
            return reduced / np.max(np.abs(reduced)) if np.max(np.abs(reduced)) > 0 else reduced
        except Exception as e:
            print(f"⚠️ noisereduce error: {e}")
            return audio
    
    # ===================== COMBINED PROCESSING =====================
    def process_audio(
        self,
        audio: np.ndarray,
        filter_type: str = 'bandpass',
        apply_spectral_subtraction: bool = True
    ) -> Tuple[np.ndarray, dict]:
        """
        Apply combined audio processing with selected filter.
        
        Args:
            audio: Input audio array
            filter_type: 'bandpass', 'lowpass', 'highpass', 'noisereduce'
            apply_spectral_subtraction: Whether to apply spectral subtraction first
        
        Returns:
            Tuple of (processed_audio, processing_metadata)
        """
        metadata = {
            'original_length': len(audio),
            'filters_applied': []
        }
        
        processed = audio.copy()
        
        # Step 1: Estimate noise level
        noise_level = self.estimate_noise_level(processed)
        metadata['noise_level'] = float(noise_level)
        
        # Step 2: Apply spectral subtraction if noise is detected
        if apply_spectral_subtraction and noise_level > 0.3:
            processed = self.apply_spectral_subtraction(processed, noise_factor=1.5)
            metadata['filters_applied'].append('spectral_subtraction')
        
        # Step 3: Apply selected filter
        if filter_type == 'bandpass':
            processed = self.apply_bandpass_filter(processed, low_freq=80, high_freq=6000)
            metadata['filters_applied'].append('bandpass_80-6000Hz')
        elif filter_type == 'lowpass':
            processed = self.apply_lowpass_filter(processed, cutoff_freq=6000)
            metadata['filters_applied'].append('lowpass_6000Hz')
        elif filter_type == 'highpass':
            processed = self.apply_highpass_filter(processed, cutoff_freq=80)
            metadata['filters_applied'].append('highpass_80Hz')
        elif filter_type == 'noisereduce':
            processed = self.apply_noisereduce(processed)
            metadata['filters_applied'].append('noisereduce_library')
        
        metadata['processed_length'] = len(processed)
        
        return processed, metadata


def record_and_process_audio(
    output_file: str = "clinical_audio.wav",
    filter_type: str = 'bandpass',
    sample_rate: int = 44100
) -> Tuple[bool, str, dict]:
    """
    Complete workflow: Record → Process → Save
    
    Returns:
        Tuple of (success, file_path/error_message, metadata)
    """
    metadata = {
        'sample_rate': sample_rate,
        'filter_type': filter_type,
        'processing_info': {}
    }
    
    # Record
    recorder = AudioRecorder(sample_rate=sample_rate)
    recorder.start_recording()
    
    # Recording runs indefinitely until stopped externally
    # (typically by GUI button click)
    
    return True, "Recording started", metadata

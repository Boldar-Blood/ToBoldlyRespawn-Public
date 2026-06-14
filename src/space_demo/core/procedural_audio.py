# Procedural Chiptune Audio Synthesis Engine - To Boldly Respawn
# Synthesizes retro sci-fi sound effects and loopable music using pure-Python standard libraries.

import os
import math
import struct
import wave
import random

SAMPLE_RATE = 44100

def save_wav(filename, samples):
    """Saves a list of float samples (-1.0 to 1.0) as a 16-bit mono PCM WAV file."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with wave.open(filename, "wb") as wav_file:
        wav_file.setnchannels(1) # Mono
        wav_file.setsampwidth(2) # 16-bit
        wav_file.setframerate(SAMPLE_RATE)
        
        packed_samples = bytearray()
        for sample in samples:
            # Clamp sample to safety limits
            sample = max(-1.0, min(1.0, sample))
            # Convert float sample to 16-bit signed integer
            val = int(sample * 32767)
            packed_samples.extend(struct.pack("<h", val))
            
        wav_file.writeframes(packed_samples)

def synth_laser():
    """Generates a retro space laser frequency sweep."""
    duration = 0.12
    num_samples = int(duration * SAMPLE_RATE)
    samples = []
    phase = 0.0
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        # Sweep frequency exponentially from 1200Hz to 150Hz
        freq = 1200.0 * math.exp(-15.0 * t)
        phase += 2.0 * math.pi * freq / SAMPLE_RATE
        
        # Sine wave with exponential decay envelope
        envelope = math.exp(-8.0 * t / duration)
        samples.append(math.sin(phase) * envelope * 0.4)
    return samples

def synth_missile():
    """Generates a low-frequency rising rocket thrust sweep with low rumble noise."""
    duration = 0.35
    num_samples = int(duration * SAMPLE_RATE)
    samples = []
    phase = 0.0
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        # Sweep from 80Hz to 400Hz
        freq = 80.0 + (320.0 * (t / duration))
        phase += 2.0 * math.pi * freq / SAMPLE_RATE
        
        # Mix in low frequency noise for thruster rumble
        noise = random.uniform(-0.15, 0.15)
        # Envelope: quick attack, slow decay
        envelope = math.exp(-3.0 * t / duration)
        samples.append((math.sin(phase) + noise) * envelope * 0.5)
    return samples

def synth_explosion():
    """Generates an white-noise blast with exponential decay."""
    duration = 0.55
    num_samples = int(duration * SAMPLE_RATE)
    samples = []
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        # Raw noise sample
        noise = random.uniform(-1.0, 1.0)
        # Fast decay envelope
        envelope = math.exp(-6.0 * t / duration)
        samples.append(noise * envelope * 0.4)
    return samples

def synth_pickup():
    """Generates an ascending retro square-wave chiptune arpeggio."""
    duration = 0.22
    num_samples = int(duration * SAMPLE_RATE)
    samples = []
    phase = 0.0
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        # Arpeggiate notes (C5 -> E5 -> G5 -> C6)
        if t < 0.05:
            freq = 523.25 # C5
        elif t < 0.10:
            freq = 659.25 # E5
        elif t < 0.15:
            freq = 783.99 # G5
        else:
            freq = 1046.50 # C6
            
        phase += 2.0 * math.pi * freq / SAMPLE_RATE
        # Square wave sound
        sq_sample = 0.15 if math.sin(phase) >= 0.0 else -0.15
        envelope = math.exp(-4.0 * t / duration)
        samples.append(sq_sample * envelope)
    return samples

def synth_alarm():
    """Generates a repeating emergency warning beep."""
    duration = 0.60
    num_samples = int(duration * SAMPLE_RATE)
    samples = []
    phase = 0.0
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        # Alternating siren frequency (450Hz / 600Hz)
        freq = 450.0 if int(t * 10) % 2 == 0 else 600.0
        phase += 2.0 * math.pi * freq / SAMPLE_RATE
        
        # Soft sine alarm sound
        alarm_env = 0.3 if (int(t * 5) % 2 == 0) else 0.0
        samples.append(math.sin(phase) * alarm_env)
    return samples

def synth_menu_music():
    """Synthesizes a loopable, slow, majestic ambient space chiptune track (8.0 seconds)."""
    duration = 8.0
    num_samples = int(duration * SAMPLE_RATE)
    samples = [0.0] * num_samples
    
    # Sequence settings
    chord_progression = [
        [261.63, 329.63, 392.00], # C Major (C4, E4, G4)
        [293.66, 349.23, 440.00], # D Minor (D4, F4, A4)
        [220.00, 261.63, 329.63], # A Minor (A3, C4, E4)
        [349.23, 440.00, 523.25]  # F Major (F4, A4, C5)
    ]
    bass_notes = [130.81, 146.83, 110.00, 174.61] # C3, D3, A2, F3
    
    # 1. Synthesize Chord Pads (Slow rising/falling warm sine waves)
    for chord_idx, chord in enumerate(chord_progression):
        chord_start = int(chord_idx * 2.0 * SAMPLE_RATE)
        chord_len = int(2.0 * SAMPLE_RATE)
        
        # Synthesize notes in the chord
        for note_freq in chord:
            phase = 0.0
            for i in range(chord_len):
                idx = chord_start + i
                t = i / SAMPLE_RATE
                phase += 2.0 * math.pi * note_freq / SAMPLE_RATE
                
                # Attack/Decay envelope for each chord (fade in/out)
                envelope = math.sin(math.pi * (t / 2.0))
                samples[idx] += math.sin(phase) * envelope * 0.12
                
    # 2. Synthesize Bassline (Slow square wave)
    for bass_idx, note_freq in enumerate(bass_notes):
        bass_start = int(bass_idx * 2.0 * SAMPLE_RATE)
        bass_len = int(2.0 * SAMPLE_RATE)
        phase = 0.0
        for i in range(bass_len):
            idx = bass_start + i
            phase += 2.0 * math.pi * note_freq / SAMPLE_RATE
            
            sq_sample = 0.06 if math.sin(phase) >= 0.0 else -0.06
            t = i / SAMPLE_RATE
            # Bass pluck envelope
            envelope = math.exp(-2.0 * t / 2.0)
            samples[idx] += sq_sample * envelope
            
    # 3. Add a simple majestic floating lead melody (Sine wave)
    melody_prog = [
        392.00, 440.00, 523.25, 587.33, # G4, A4, C5, D5
        523.25, 440.00, 392.00, 349.23  # C5, A4, G4, F4
    ]
    for m_idx, note_freq in enumerate(melody_prog):
        m_start = int(m_idx * 1.0 * SAMPLE_RATE)
        m_len = int(1.0 * SAMPLE_RATE)
        phase = 0.0
        for i in range(m_len):
            idx = m_start + i
            t = i / SAMPLE_RATE
            phase += 2.0 * math.pi * note_freq / SAMPLE_RATE
            
            lead_env = math.sin(math.pi * (t / 1.0)) * 0.05
            samples[idx] += math.sin(phase) * lead_env
            
    return samples

def synth_chase_music():
    """Synthesizes a fast, driving, loopable retrograde pursuit chiptune track (6.0 seconds, 140 BPM)."""
    duration = 6.0
    num_samples = int(duration * SAMPLE_RATE)
    samples = [0.0] * num_samples
    
    # 140 BPM = ~0.428s per beat, 16 steps per bar, ~0.107s per step
    step_duration = 0.107
    step_len = int(step_duration * SAMPLE_RATE)
    
    # Drum sequences (1 = trigger, 0 = silence)
    kick_seq = [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0] # 4-on-the-floor
    hat_seq =  [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0] # Off-beat hi-hat
    
    # E-minor driving bassline (repeating frequencies)
    bass_freqs = [82.41, 82.41, 98.00, 82.41, 110.00, 82.41, 73.42, 82.41] # E2, E2, G2, E2, A2, E2, D2, E2
    
    # Lead arpeggio melody
    lead_notes = [329.63, 392.00, 440.00, 493.88, 392.00, 440.00, 493.88, 587.33] # E4, G4, A4, B4, G4, A4, B4, D5
    
    total_steps = int(duration / step_duration)
    
    # Drum synthesis state
    for step in range(total_steps):
        step_start = step * step_len
        
        # 1. Kick drum (Rapid pitch sweep from 140Hz to 30Hz)
        if kick_seq[step % 16]:
            for i in range(min(step_len, 4000)):
                idx = step_start + i
                t = i / SAMPLE_RATE
                freq = 140.0 * math.exp(-35.0 * t)
                if freq < 30.0: freq = 30.0
                envelope = math.exp(-12.0 * t / 0.15)
                samples[idx] += math.sin(2.0 * math.pi * freq * t) * envelope * 0.28
                
        # 2. Closed Hi-hat (Very short white noise burst)
        if hat_seq[step % 16]:
            for i in range(min(step_len, 1200)):
                idx = step_start + i
                t = i / SAMPLE_RATE
                noise = random.uniform(-1.0, 1.0)
                envelope = math.exp(-40.0 * t / 0.05)
                samples[idx] += noise * envelope * 0.08
                
        # 3. Driving Square Bassline (Fast syncopated notes)
        bass_note = bass_freqs[step % 8]
        phase = 0.0
        for i in range(step_len):
            idx = step_start + i
            phase += 2.0 * math.pi * bass_note / SAMPLE_RATE
            
            sq_val = 0.08 if math.sin(phase) >= 0.0 else -0.08
            t = i / SAMPLE_RATE
            envelope = math.exp(-6.0 * t / step_duration)
            samples[idx] += sq_val * envelope
            
        # 4. Melodic lead sequence (Syncopated triangle wave)
        lead_note = lead_notes[(step // 2) % 8]
        # Only play on alternate steps for syncopation
        if step % 2 == 1:
            phase = 0.0
            for i in range(step_len):
                idx = step_start + i
                phase += 2.0 * math.pi * lead_note / SAMPLE_RATE
                
                # Triangle wave synthesis
                phase_mod = phase % (2.0 * math.pi)
                tri_val = (phase_mod / math.pi) - 1.0 if phase_mod < math.pi else 3.0 - (phase_mod / math.pi)
                
                t = i / SAMPLE_RATE
                envelope = math.exp(-4.0 * t / step_duration)
                samples[idx] += tri_val * envelope * 0.06
                
    return samples

def generate_all_audio():
    """Generates all procedural WAV audio files under data/ folder if they do not exist."""
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data"))
    
    audio_assets = {
        "laser.wav": synth_laser,
        "missile.wav": synth_missile,
        "explosion.wav": synth_explosion,
        "pickup.wav": synth_pickup,
        "alarm.wav": synth_alarm,
        "menu_music.wav": synth_menu_music,
        "chase_music.wav": synth_chase_music
    }
    
    print("[Audio Engine] Synthesizing chiptune audio assets... (Wait a moment)")
    for filename, synth_func in audio_assets.items():
        filepath = os.path.join(data_dir, filename)
        if not os.path.exists(filepath):
            try:
                samples = synth_func()
                save_wav(filepath, samples)
                print(f"[Audio Engine] Synthesized successfully: {filename}")
            except Exception as e:
                print(f"[Audio Engine] Failed to synthesize {filename}: {e}")
        else:
            print(f"[Audio Engine] Asset already exists: {filename}")
    print("[Audio Engine] Synthesize run completed.")

if __name__ == "__main__":
    generate_all_audio()

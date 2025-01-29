import json
import pandas as pd
from glob import glob
from tqdm.auto import tqdm
from pathlib import Path

import librosa
import soundfile as sf
from pydub import AudioSegment
import google.generativeai as genai


prompt = "Please transcribe the given recorded interview speech."

def convert_mp4_to_wav(input_path, output_path=None):
   """Convert MP4 video to WAV audio using librosa"""
   if output_path is None:
       output_path = input_path.rsplit('.', 1)[0] + '.wav'

   # Load audio and convert to wav
   y, sr = librosa.load(input_path)
   sf.write(output_path, y, sr)
   print(f"Converted {input_path} to {output_path}")


def split_audio(audio_path, output_folder, duration=300, overlap=30):
    """
    Split audio file into segments with specified duration and overlap interval.
    
    Parameters:
        audio_path (str): Path to input audio file
        output_folder (str): Directory to save segments
        duration (int): Duration of each segment in seconds (default: 300)
        overlap (int): Overlap interval between segments in seconds (default: 30)
    """
    # Create output directory using pathlib
    output_dir = Path(output_folder)
    output_dir.mkdir(exist_ok=True)

    print(f"Loading: {audio_path}")
    audio = AudioSegment.from_file(audio_path)

    # Convert to milliseconds
    duration_ms = duration * 1000
    overlap_ms = overlap * 1000
    
    # Calculate step size (duration - overlap)
    step_ms = duration_ms - overlap_ms
    
    # Process segments
    segments = []
    for i, start in enumerate(range(0, len(audio) - overlap_ms, step_ms)):
        end = start + duration_ms
        if end > len(audio):
            end = len(audio)

        segment = audio[start:end]
        path = output_dir / f"segment_{i+1:02d}.wav"
        segments.append((i, segment, path))

    # Export segments
    for i, segment, path in segments:
        segment.export(path, format="wav")
        print(f"Segment {i+1} saved: {path}")
    
    print("Audio splitting completed.")


def transcribe_audio_folder(model, folder_path, prompt="Please transcribe the given recorded speech in Thai and English."):
    """
    Transcribe all WAV files in a folder using Google's Generative AI.
    
    Args:
        folder_path (str): Path to folder containing WAV files
        prompt (str): Prompt for the transcription (default: "Generate a transcript of the speech.")
    
    Returns:
        pd.DataFrame: DataFrame containing audio filenames and their transcriptions
    """
    # Ensure folder path is valid
    folder = Path(folder_path)
    if not folder.exists():
        raise ValueError(f"Folder not found: {folder_path}")
    
    # Get all WAV files in the folder
    audio_files = list(folder.glob("*.wav"))
    if not audio_files:
        raise ValueError(f"No WAV files found in {folder_path}")
    
    transcriptions = []
    
    # Process each audio file
    for audio_file in tqdm(audio_files, desc="Transcribing audio files"):
        try:            
            # Upload and process audio file
            audio_upload = genai.upload_file(str(audio_file))
            response = model.generate_content([prompt, audio_upload])
            transcription = response.text.replace("```json", "").replace("```", "").strip()
            transcriptions.append({
                "audio_file": audio_file.name,
                "text": transcription
            })
        except Exception as e:
            print(f"Error processing {audio_file.name}: {str(e)}")
            transcriptions.append({
                "audio_file": audio_file.name,
                "text": f"ERROR: {str(e)}"
            })

    # Convert to DataFrame
    return pd.DataFrame(transcriptions)
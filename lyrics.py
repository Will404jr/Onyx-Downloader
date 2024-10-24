import speech_recognition as sr
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
import os

def video_to_audio(video_path):
    """Convert video to audio (MP3)"""
    video = VideoFileClip(video_path)
    audio_path = "temp_audio.mp3"
    video.audio.write_audiofile(audio_path)
    return audio_path

def convert_mp3_to_wav(mp3_path):
    """Convert MP3 file to WAV format"""
    audio = AudioSegment.from_mp3(mp3_path)
    wav_path = mp3_path.replace(".mp3", ".wav")
    audio.export(wav_path, format="wav")
    return wav_path

def audio_to_text(audio_path):
    """Convert audio (WAV) to text using SpeechRecognition"""
    recognizer = sr.Recognizer()
    
    # Load audio file
    audio_file = sr.AudioFile(audio_path)
    
    with audio_file as source:
        audio_data = recognizer.record(source)
    
    try:
        # Use Google's API to recognize speech
        text = recognizer.recognize_google(audio_data)
        return text
    except sr.UnknownValueError:
        return "Could not understand the audio."
    except sr.RequestError:
        return "Could not request results from the speech recognition service."

def convert_media_to_text(media_path):
    """Main function to convert media (video or audio) to text"""
    extension = os.path.splitext(media_path)[1].lower()
    
    # If it's a video file, convert it to audio
    if extension in ['.mp4', '.avi', '.mkv', '.mov']:
        audio_path = video_to_audio(media_path)
        wav_path = convert_mp3_to_wav(audio_path)
    elif extension == '.mp3':
        wav_path = convert_mp3_to_wav(media_path)
    elif extension == '.wav':
        wav_path = media_path
    else:
        raise ValueError("Unsupported file format. Please provide a video, mp3, or wav file.")
    
    # Convert the audio to text
    text = audio_to_text(wav_path)
    
    # Clean up temp audio files if created
    if extension in ['.mp4', '.avi', '.mkv', '.mov', '.mp3']:
        os.remove(wav_path)  # Remove the WAV file generated from MP3
        if extension in ['.mp4', '.avi', '.mkv', '.mov']:
            os.remove(audio_path)  # Remove the MP3 file generated from video
    
    return text

if __name__ == "__main__":
    media_path = input("Enter the path to your video or audio file: ")
    result_text = convert_media_to_text(media_path)
    print("Extracted Text/Lyrics:\n", result_text)

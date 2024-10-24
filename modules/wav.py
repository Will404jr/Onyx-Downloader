from pydub import AudioSegment

# Convert MP3 to WAV
audio_path_mp3 = r'C:\Users\Will\Desktop\Code Python\Onyx app\outputs\Guvna.mp3'
audio_path_wav = r'C:\Users\Will\Desktop\Code Python\Onyx app\outputs\Guvna.wav'

audio = AudioSegment.from_mp3(audio_path_mp3)
audio.export(audio_path_wav, format="wav")

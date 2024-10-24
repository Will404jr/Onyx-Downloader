import os
import shutil
import yt_dlp

# Define the playlist URL and directory
playlist_url = 'https://youtube.com/playlist?list=PLfG0lepGdWQIvEbVGP3DBkSCGWXwo1T2d&si=5DkCbJdPK7anNcCc'        
download_dir = 'YouTube_Playlist3'

# Create the directory if it doesn't exist
os.makedirs(download_dir, exist_ok=True)

# Download the playlist using yt-dlp
ydl_opts = {
    'format': 'best',
    'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([playlist_url])

# Zip the directory containing the downloaded videos
shutil.make_archive(download_dir, 'zip', download_dir)

print(f'Playlist downloaded and zipped successfully. Find the zip file: {download_dir}.zip')

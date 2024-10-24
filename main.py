import sys
import threading
import subprocess
import time  # New import for simulating progress
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QProgressBar, QComboBox, QFileDialog, QToolBar
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QAction
import yt_dlp
import os
import logging

# Set up basic logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DownloadSignals(QObject):
    progress = pyqtSignal(float)
    status = pyqtSignal(str)

class VideoDownloaderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Downloader")
        self.setFixedSize(600, 500)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e2e;
            }
            QLabel {
                color: #cdd6f4;
                font-size: 16px;
            }
            QLineEdit {
                background-color: #313244;
                color: #cdd6f4;
                border: 2px solid #89b4fa;
                border-radius: 10px;
                padding: 5px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #89b4fa;
                color: #1e1e2e;
                border: none;
                border-radius: 10px;
                padding: 10px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #b4befe;
            }
            QProgressBar {
                background-color: #313244;
                border: 2px solid #89b4fa;
                border-radius: 10px;
                color: #1e1e2e;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #a6e3a1;
                border-radius: 8px;
            }
            QComboBox {
                background-color: #313244;
                color: #cdd6f4;
                border: 2px solid #89b4fa;
                border-radius: 10px;
                padding: 5px;
                font-size: 14px;
            }
            QToolBar {
                background-color: #1e1e2e;
                border-bottom: 2px solid #89b4fa;
            }
            QToolBar QToolButton {
                color: #cdd6f4;
                font-size: 16px;
                padding: 5px;
            }
            QToolBar QToolButton:hover {
                background-color: #313244;
            }
        """)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(20)

        self.create_toolbar()

        self.title = QLabel("Video Downloader")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("font-size: 28px; font-weight: bold; color: #f5c2e7;")
        self.layout.addWidget(self.title)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter video URL")
        self.url_input.textChanged.connect(self.check_url_type)
        self.layout.addWidget(self.url_input)

        self.select_file_button = QPushButton("Select File")
        self.select_file_button.clicked.connect(self.select_file)
        self.select_file_button.hide()  # Hidden by default, shown in MP3 converter mode
        self.layout.addWidget(self.select_file_button)

        self.format_combo = QComboBox()
        self.layout.addWidget(self.format_combo)

        self.download_button = QPushButton("Download")
        self.download_button.clicked.connect(self.start_download)
        self.layout.addWidget(self.download_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready to download")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.status_label)

        self.signals = DownloadSignals()
        self.signals.progress.connect(self.update_progress)
        self.signals.status.connect(self.update_status)

        # Predefine the formats for YouTube videos
        self.formats = [('240p', '18'), ('360p', '18'), ('480p', '135'), ('720p', '136'), ('1080p', '137'), ('1440p', '271')]
        for fmt in self.formats:
            self.format_combo.addItem(fmt[0])

        self.is_youtube_url = False

        # Ensure the outputs directory exists
        self.output_dir = os.path.join(os.path.dirname(__file__), 'outputs')
        os.makedirs(self.output_dir, exist_ok=True)

    def create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        video_downloader_action = QAction("Video Downloader", self)
        video_downloader_action.triggered.connect(self.show_video_downloader)
        toolbar.addAction(video_downloader_action)

        mp3_converter_action = QAction("MP3 Converter", self)
        mp3_converter_action.triggered.connect(self.show_mp3_converter)
        toolbar.addAction(mp3_converter_action)

        playlist_downloader_action = QAction("Playlist Downloader", self)
        playlist_downloader_action.triggered.connect(self.show_playlist_downloader)
        toolbar.addAction(playlist_downloader_action)

    def show_video_downloader(self):
        self.title.setText("Video Downloader")
        self.url_input.setPlaceholderText("Enter video URL")
        self.url_input.clear()  # Clear the input field
        self.url_input.show()
        self.select_file_button.hide()
        self.format_combo.show()  # Show format combo in video downloader mode
        self.download_button.setText("Download")
        self.download_button.clicked.disconnect()
        self.download_button.clicked.connect(self.start_download)
        self.url_input.textChanged.connect(self.check_url_type)  # Connect signal

    def show_mp3_converter(self):
        self.title.setText("MP3 Converter")
        self.url_input.setPlaceholderText("Enter video URL or select a file")
        self.url_input.clear()  # Clear the input field
        self.url_input.show()
        self.select_file_button.show()
        self.format_combo.hide()  # Hide format combo in MP3 converter mode
        self.download_button.setText("Convert to MP3")
        self.download_button.clicked.disconnect()
        self.download_button.clicked.connect(self.start_mp3_conversion)
        
        # Safely attempt to disconnect the signal
        try:
            self.url_input.textChanged.disconnect(self.check_url_type)
        except TypeError:
            pass  # Ignore if the signal was not connected

    def select_file(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Select Video File", "", "Video Files (*.mp4 *.mkv *.avi *.mov)")
        if file_path:
            self.url_input.setText(file_path)

    def check_url_type(self):
        url = self.url_input.text()
        # Check if the URL is from YouTube
        if 'youtube.com' in url or 'youtu.be' in url:
            self.is_youtube_url = True
            if self.title.text() == "Video Downloader":  # Only show in Video Downloader mode
                self.format_combo.show()
        else:
            self.is_youtube_url = False
            self.format_combo.hide()

    def start_download(self):
        url = self.url_input.text()
        if self.is_youtube_url:
            selected_index = self.format_combo.currentIndex()
            if url and selected_index >= 0:
                format_id = self.formats[selected_index][1]
                self.status_label.setText(f"Starting download for format {format_id}...")
                threading.Thread(target=self.download_video, args=(url, format_id), daemon=True).start()
            else:
                self.status_label.setText("Please enter a valid URL and select a format")
        else:
            self.status_label.setText(f"Downloading non-YouTube video...")
            threading.Thread(target=self.download_non_youtube_video, args=(url,), daemon=True).start()

    def start_mp3_conversion(self):
        source = self.url_input.text()
        if os.path.isfile(source):  # Check if the input is a local file
            self.status_label.setText("Converting from file...")
            threading.Thread(target=self.convert_local_to_mp3, args=(source,), daemon=True).start()
        elif source.startswith("http"):
            self.status_label.setText("Converting from URL...")
            threading.Thread(target=self.convert_url_to_mp3, args=(source,), daemon=True).start()
        else:
            self.status_label.setText("Please enter a valid URL or select a file")

    def convert_local_to_mp3(self, file_path):
        # Get the total duration of the video using ffprobe
        command = [
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of",
            "default=noprint_wrappers=1:nokey=1", file_path
        ]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, _ = process.communicate()
        total_duration = float(stdout.strip())

        output_path = os.path.join(self.output_dir, os.path.splitext(os.path.basename(file_path))[0] + ".mp3")
        command = [
            "ffmpeg", "-i", file_path, "-vn", "-acodec", "libmp3lame", "-q:a", "2", output_path
        ]

        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        
        # Monitor ffmpeg output for progress
        for line in process.stderr:
            if "time=" in line:
                time_info = line.split("time=")[1].split()[0]
                h, m, s = time_info.split(':')
                current_time = int(h) * 3600 + int(m) * 60 + float(s)
                progress = min(100, (current_time / total_duration) * 100)
                self.signals.progress.emit(progress)

        process.wait()
        
        if process.returncode == 0:
            self.signals.progress.emit(100)
            self.signals.status.emit("MP3 Conversion complete!")
        else:
            error_output = process.stderr.read()
            self.signals.status.emit(f"Error: Conversion failed. {error_output}")

        # Reset the progress bar after conversion
        self.progress_bar.setValue(0)

    def download_video(self, url, format_id):
        ydl_opts = {
            'format': f'{format_id}+bestaudio/best',
            'outtmpl': os.path.join(self.output_dir, '%(title)s.%(ext)s'),
            'progress_hooks': [self.hook]
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.signals.status.emit("Download complete!")
        except Exception as e:
            self.signals.status.emit(f"Error: {str(e)}")

    def hook(self, d):
        if d['status'] == 'downloading':
            progress = d.get('downloaded_bytes', 0) / d.get('total_bytes', 1) * 100
            self.signals.progress.emit(progress)
        elif d['status'] == 'finished':
            self.signals.status.emit("MP3 Conversion complete!")

    def update_progress(self, value):
        self.progress_bar.setValue(int(value))

    def update_status(self, message):
        self.status_label.setText(message)
        if message == "MP3 Conversion complete!" or message == "Download complete!":
            self.progress_bar.setValue(0)  # Reset the progress bar after completion

    def download_non_youtube_video(self, url):
        import yt_dlp

        ydl_opts = {
            'outtmpl': os.path.join(self.output_dir, '%(title)s.%(ext)s'),
            'progress_hooks': [self.hook]
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.signals.status.emit("Download complete!")
            logging.info("Download complete!")
        except Exception as e:
            error_message = f"Error: Download failed. {str(e)}"
            self.signals.status.emit(error_message)
            logging.error(error_message)

    def convert_url_to_mp3(self, url):
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(self.output_dir, '%(title)s.%(ext)s'),
            'progress_hooks': [self.hook]
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.signals.status.emit("MP3 Conversion complete!")
        except Exception as e:
            self.signals.status.emit(f"Error: {str(e)}")

    def show_playlist_downloader(self):
        self.title.setText("Playlist Downloader")
        self.url_input.setPlaceholderText("Enter playlist URL")
        self.url_input.clear()  # Clear the input field
        self.url_input.show()
        self.select_file_button.setText("Select Output Directory")
        self.select_file_button.clicked.disconnect()
        self.select_file_button.clicked.connect(self.select_output_directory)
        self.select_file_button.show()
        self.format_combo.hide()  # Hide format combo in playlist downloader mode
        self.download_button.setText("Download Playlist")
        self.download_button.clicked.disconnect()
        self.download_button.clicked.connect(self.start_playlist_download)
        
        # Safely attempt to disconnect the signal
        try:
            self.url_input.textChanged.disconnect(self.check_url_type)
        except TypeError:
            pass  # Ignore if the signal was not connected

    def select_output_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_dir = directory

    def start_playlist_download(self):
        url = self.url_input.text()
        if url:
            self.status_label.setText("Downloading playlist...")
            threading.Thread(target=self.download_playlist, args=(url,), daemon=True).start()
        else:
            self.status_label.setText("Please enter a valid playlist URL")

    def download_playlist(self, url):
        import yt_dlp

        ydl_opts = {
            'outtmpl': os.path.join(self.output_dir, '%(playlist_title)s', '%(title)s.%(ext)s'),
            'progress_hooks': [self.hook]
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.signals.status.emit("Playlist download complete!")
            logging.info("Playlist download complete!")
        except Exception as e:
            error_message = f"Error: Playlist download failed. {str(e)}"
            self.signals.status.emit(error_message)
            logging.error(error_message)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    downloader_app = VideoDownloaderApp()
    downloader_app.show()
    sys.exit(app.exec())

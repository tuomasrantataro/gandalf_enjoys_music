from PySide2.QtCore import Slot, Signal, Qt, QUrl
from PySide2.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton
from PySide2.QtGui import QPalette
from PySide2.QtMultimedia import QMediaPlayer, QMediaPlaylist
from PySide2.QtMultimediaWidgets import QVideoWidget

class GandalfVideo(QVideoWidget):
    """Widget for showing looping video and setting its playback speed"""
    fullscreen_changed = Signal(bool)
    def __init__(self, parent, show_preview):
        super().__init__(parent)
        self.show_preview = show_preview

        self.gandalf_default_bpm = 75
        self.old_bpm = self.gandalf_default_bpm

        self.init_video()
        self.set_bpm(self.gandalf_default_bpm)

    def init_video(self):
        self.media_player = QMediaPlayer(self)
        self.media_player.setVideoOutput(self)

        pal = self.palette()
        pal.setColor(QPalette.Background, Qt.black)
        self.setAutoFillBackground(True)
        self.setPalette(pal)

        self.playlist = QMediaPlaylist(self.media_player)
        file_location = "/home/tuomas/projektit/gandalf_enjoys_music/resources/gandalf4.mp4"
        self.video_file = QUrl.fromLocalFile(file_location)
        self.playlist.addMedia(self.video_file)
        self.playlist.setPlaybackMode(QMediaPlaylist.Loop)
        self.playlist.setCurrentIndex(0)
        self.media_player.setPlaylist(self.playlist)
        self.media_player.play()

        if not self.show_preview:
            self.hide()

    def mouseDoubleClickEvent(self, event):
        if self.isFullScreen():
            if self.show_preview:
                self.setFullScreen(False)
            else:
                self.hide()
            self.fullscreen_changed.emit(False)
        else:
            self.setFullScreen(True)
            self.fullscreen_changed.emit(True)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            if self.show_preview:
                self.setFullScreen(False)
            else:
                self.hide()

    @Slot(float)
    def set_bpm(self, bpm):
        """Update playback speed for Gandalf video loop."""
        bpm = int(bpm+0.5)
        if bpm != self.old_bpm:
            print("BPM updated:", bpm)
            self.old_bpm = bpm
            gandalf_speed = bpm / self.gandalf_default_bpm
            current_position = self.media_player.position()
            self.media_player.setPlaybackRate(gandalf_speed)
            self.media_player.setPosition(current_position+100)
            self.media_player.play()

class MainWindow(QMainWindow):
    """Display nodding Gandalf loop and controls"""
    show_preview = True
    def __init__(self, parent=None):
        super().__init__(parent)

        self.central = QWidget(self)
        self.setCentralWidget(self.central)
        self.layout = QVBoxLayout()

        self.video_widget = GandalfVideo(self, self.show_preview)

        if self.show_preview:
            self.layout.addWidget(self.video_widget)
        else:
            self.fullscreen_button = QPushButton()
            self.fullscreen_button.setText("Go Fullscreen")
            self.layout.addWidget(self.fullscreen_button)
            self.fullscreen_button.clicked.connect(self.show_fullscreen)
            self.video_widget.fullscreen_changed.connect(
                self.update_button_text)

        self.central.setLayout(self.layout)

    def set_bpm(self, bpm):
        self.video_widget.set_bpm(bpm)

    @Slot()
    def show_fullscreen(self):
        if self.video_widget.isFullScreen():
            self.video_widget.hide()
            self.fullscreen_button.setText("Go Fullscreen")
        else:
            self.video_widget.setFullScreen(True)
            self.fullscreen_button.setText("Hide Fullscreen")

    @Slot(bool)
    def update_button_text(self, fullscreen_status):
        if fullscreen_status:
            self.fullscreen_button.setText("Hide Fullscreen")
        else:
            self.fullscreen_button.setText("Go Fullscreen")

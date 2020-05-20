import os
import json

from PySide2.QtCore import Qt, QUrl, Signal, Slot
from PySide2.QtGui import QPalette
from PySide2.QtMultimedia import QMediaPlayer, QMediaPlaylist
from PySide2.QtMultimediaWidgets import QVideoWidget
from PySide2.QtWidgets import (QCheckBox, QComboBox, QHBoxLayout, QLabel,
                               QLineEdit, QMainWindow, QPushButton,
                               QVBoxLayout, QWidget)

from audio_device import AudioDevice
from bpm_helper import BPMQt, BPMmp


class VideoWidget(QVideoWidget):
    fullscreen_changed = Signal(bool)
    def __init__(self, parent, show_preview):
        super().__init__(parent)
        self.show_preview = show_preview

        self.pal = self.palette()
        self.pal.setColor(QPalette.Background, Qt.black)
        self.setAutoFillBackground(True)
        self.setPalette(self.pal)

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
            self.fullscreen_changed.emit(False)

class MainWindow(QMainWindow):
    """Display video loop and controls"""
    audio_changed = Signal(str)
    def __init__(self, parent=None):
        super().__init__(parent)

        # Default values. Updated if found in config.JSON
        self.use_qt_thread = False
        self.rhythm_algorithm = "multifeature"
        self.default_device_name = ""
        self.show_video_preview = True
        self.video_loop_bpm = 60
        self.video_update_skip_ms = 100

        self.read_config()

        self.setWindowTitle("Gandalf Enjoys Music")

        self.audio = AudioDevice(self.default_device_name)
        self.input_devices = self.audio.get_input_device_names()

        self.audio_changed.connect(self.audio.change_audio_input)

        if self.use_qt_thread:
            self.bpm_extractor = BPMQt(self.update_bpm,
                                       algorithm=self.rhythm_algorithm)
        else:
            self.bpm_extractor = BPMmp(self.update_bpm,
                                       algorithm=self.rhythm_algorithm)

        self.audio.data_ready.connect(self.bpm_extractor.start_bpm_calculation)

        self.init_ui()

    def init_ui(self):
        self.central = QWidget(self)
        self.setCentralWidget(self.central)
        self.layout = QVBoxLayout()

        self.init_video()

        if self.show_video_preview:
            self.layout.addWidget(self.video_widget)
        else:
            self.fullscreen_button = QPushButton(self)
            self.fullscreen_button.setText("Go Fullscreen")
            self.layout.addWidget(self.fullscreen_button)
            self.fullscreen_button.clicked.connect(self.show_fullscreen)
            self.video_widget.fullscreen_changed.connect(
                self.update_button_text)

        self.control_layout = QHBoxLayout()

        self.lock_checkbox = QCheckBox("Manual tempo", self)
        self.lock_checkbox.clicked.connect(self.update_lock_checkbox)
        self.control_layout.addWidget(self.lock_checkbox)

        self.set_bpm_widget = QLineEdit("{:.1f}".format(self.old_bpm), self)
        self.set_bpm_widget.setMaxLength(5)
        self.set_bpm_widget.returnPressed.connect(self.update_bpm_manually)
        self.set_bpm_palette = QPalette()
        self.set_bpm_palette.setColor(QPalette.Text, Qt.gray)
        self.set_bpm_widget.setPalette(self.set_bpm_palette)
        self.set_bpm_widget.setFixedWidth(50)
        self.control_layout.addWidget(self.set_bpm_widget)

        self.limit_checkbox = QCheckBox("Limit tempo between:", self)
        self.control_layout.addWidget(self.limit_checkbox)

        self.lower_bpm_limit = 60.0
        self.lower_bpm_widget = QLineEdit(str(self.lower_bpm_limit), self)
        self.lower_bpm_widget.setMaxLength(5)
        self.lower_bpm_widget.returnPressed.connect(self.update_lower_limit)
        self.lower_bpm_widget.setFixedWidth(50)
        self.control_layout.addWidget(self.lower_bpm_widget)

        self.upper_bpm_limit = 120.0
        self.upper_bpm_widget = QLineEdit(str(self.upper_bpm_limit), self)
        self.upper_bpm_widget.setMaxLength(5)
        self.upper_bpm_widget.returnPressed.connect(self.update_upper_limit)
        self.upper_bpm_widget.setFixedWidth(50)
        self.control_layout.addWidget(self.upper_bpm_widget)

        self.layout.addLayout(self.control_layout)  

        self.device_layout = QHBoxLayout()
        self.audio_select_label = QLabel("Audio device:", self)
        self.device_layout.addWidget(self.audio_select_label)

        self.audio_selection = QComboBox(self)
        self.audio_selection.addItems(self.input_devices)
        self.audio_selection.currentIndexChanged.connect(self.audio_selection_changed)
        self.device_layout.addWidget(self.audio_selection)

        self.layout.addLayout(self.device_layout)

        self.central.setLayout(self.layout)

    def init_video(self):
        self.old_bpm = 1.0

        self.video_widget = VideoWidget(self, self.show_video_preview)
        self.media_player = QMediaPlayer(self.central)
        self.media_player.setVideoOutput(self.video_widget)

        self.playlist = QMediaPlaylist(self.media_player)
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file_location = dir_path + "/resources/video_long.mp4"
        self.video_file = QUrl.fromLocalFile(file_location)
        self.playlist.addMedia(self.video_file)
        self.playlist.setPlaybackMode(QMediaPlaylist.Loop)
        self.playlist.setCurrentIndex(0)
        self.media_player.setPlaylist(self.playlist)
        self.media_player.mediaStatusChanged.connect(self.handle_media_state_changed)

        self.media_player.play()

        self.change_playback_rate(self.video_loop_bpm)

        if not self.show_video_preview:
            self.video_widget.hide()

    def handle_media_state_changed(self, state):
        if state == QMediaPlayer.MediaStatus.BufferedMedia:
            playback_speed = self.old_bpm / self.video_loop_bpm
            self.media_player.setPlaybackRate(playback_speed)
            self.media_player.setPosition(0)

    def change_playback_rate(self, bpm):
        """Update playback speed for video loop."""
        if bpm != self.old_bpm:
            self.old_bpm = bpm
            playback_speed = bpm / self.video_loop_bpm

            # Workaround for a bug which causes irregular video playback speed
            # after changing playback rate
            current_position = self.media_player.position()
            self.media_player.setPlaybackRate(playback_speed)
            self.media_player.setPosition(current_position
                                          + self.video_update_skip_ms)

    def update_bpm(self, bpm, manual=False):
        if not manual:
            if self.lock_checkbox.isChecked():
                return
            bpm = float(int(bpm+0.5))
        if self.limit_checkbox.isChecked():
            while bpm < self.lower_bpm_limit:
                bpm = bpm * 2.0
            while bpm > self.upper_bpm_limit:
                bpm = bpm / 2.0
        self.change_playback_rate(bpm)
        self.set_bpm_widget.setText("{:.1f}".format(self.old_bpm))

    def update_bpm_manually(self):
        bpm = self.set_bpm_widget.text()
        try:
            bpm = float(bpm)
            if bpm < 1.0:
                raise ValueError
        except ValueError:
            return
        self.update_bpm(bpm, manual=True)

    def update_lock_checkbox(self):
        if self.lock_checkbox.isChecked():
            self.set_bpm_palette = QPalette()
            self.set_bpm_palette.setColor(QPalette.Text, Qt.black)
            self.set_bpm_widget.setPalette(self.set_bpm_palette)
            self.set_bpm_widget.setReadOnly(False)
        else:
            self.set_bpm_palette = QPalette()
            self.set_bpm_palette.setColor(QPalette.Text, Qt.gray)
            self.set_bpm_widget.setPalette(self.set_bpm_palette)
            self.set_bpm_widget.setReadOnly(True)

    def update_lower_limit(self):
        value = self.lower_bpm_widget.text()
        try:
            value = float(value)
            if value < 1.0:
                raise ValueError
        except ValueError:
            return
        if value <= self.upper_bpm_limit / 2.0:
            self.lower_bpm_limit = value
        else:
            self.lower_bpm_limit = self.upper_bpm_limit / 2.0
        self.lower_bpm_widget.setText("{:.1f}".format(self.lower_bpm_limit))

    def update_upper_limit(self):
        value = self.upper_bpm_widget.text()
        try:
            value = float(value)
            if value < 1.0:
                raise ValueError
        except ValueError:
            return
        if value >= self.lower_bpm_limit * 2.0:
            self.upper_bpm_limit = value
        else:
            self.upper_bpm_limit = self.lower_bpm_limit * 2.0
        self.upper_bpm_widget.setText("{:.1f}".format(self.upper_bpm_limit))

    def audio_selection_changed(self, idx):
        self.audio_changed.emit(self.audio_selection.currentText())

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

    def read_config(self):
        with open("config.JSON") as config_file:
            config = json.load(config_file)

            if "no_multiprocess" in config:
                self.use_qt_thread = config["no_multiprocess"]
            if config.get("rhythm_algorithm_faster"):
                self.rhythm_algorithm = "degara"
            if config.get("default_device"):
                self.default_device_name = config["default_device"]
            if "show_video_preview" in config:
                self.show_video_preview = config.get("show_video_preview")
            if config.get("video_loop_bpm"):
                self.video_loop_bpm = config["video_loop_bpm"]
            if config.get("video_update_skip_time_ms"):
                self.video_update_skip_ms = config["video_update_skip_time_ms"]

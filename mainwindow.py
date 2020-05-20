import os

from PySide2.QtCore import Qt, QUrl, Signal, Slot
from PySide2.QtGui import QPalette
from PySide2.QtMultimedia import QMediaPlayer, QMediaPlaylist
from PySide2.QtMultimediaWidgets import QVideoWidget
from PySide2.QtWidgets import (QCheckBox, QComboBox, QHBoxLayout, QLabel,
                               QLineEdit, QMainWindow, QPushButton,
                               QVBoxLayout, QWidget)


class GandalfVideo(QVideoWidget):
    """Widget for showing looping video and setting its playback speed"""
    fullscreen_changed = Signal(bool)
    def __init__(self, parent, show_preview, loop_bpm, update_skip_ms):
        super().__init__(parent)
        self.show_preview = show_preview
        self.update_skip_ms = update_skip_ms

        self.gandalf_default_bpm = loop_bpm #74.2
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
        #print("dir path:", dir_path)
        #path_end = "/resources/video_long.mp4"
        #print("whole path:", dir_path + path_end)
        #file_location = "/home/tuomas/projektit/gandalf_enjoys_music/resources/video_long.mp4"
        #print("old path:", file_location)
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file_location = dir_path + "/resources/video_long.mp4"
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
            self.old_bpm = bpm
            gandalf_speed = bpm / self.gandalf_default_bpm
            current_position = self.media_player.position()
            self.media_player.setPlaybackRate(gandalf_speed)
            self.media_player.setPosition(current_position+self.update_skip_ms)
            self.media_player.play()

class MainWindow(QMainWindow):
    """Display nodding Gandalf loop and controls"""
    audio_changed = Signal(str)
    def __init__(self, show_preview, loop_bpm, update_skip_ms, input_devices,
                 parent=None):
        super().__init__(parent)
        self.show_preview = show_preview

        self.central = QWidget(self)
        self.setCentralWidget(self.central)
        self.layout = QVBoxLayout()

        self.video_widget = GandalfVideo(self,
                                         self.show_preview,
                                         loop_bpm,
                                         update_skip_ms)

        if self.show_preview:
            self.layout.addWidget(self.video_widget)
        else:
            self.fullscreen_button = QPushButton()
            self.fullscreen_button.setText("Go Fullscreen")
            self.layout.addWidget(self.fullscreen_button)
            self.fullscreen_button.clicked.connect(self.show_fullscreen)
            self.video_widget.fullscreen_changed.connect(
                self.update_button_text)

        self.control_layout = QHBoxLayout()

        self.lock_checkbox = QCheckBox("Manual tempo", self)
        self.lock_checkbox.clicked.connect(self.update_lock_checkbox)
        self.control_layout.addWidget(self.lock_checkbox)

        self.set_bpm_widget = QLineEdit("{:.1f}".format(self.video_widget.old_bpm), self)
        self.set_bpm_widget.setMaxLength(5)
        self.set_bpm_widget.returnPressed.connect(self.update_bpm_manually)
        self.set_bpm_palette = QPalette()
        self.set_bpm_palette.setColor(QPalette.Text, Qt.gray)
        self.set_bpm_widget.setPalette(self.set_bpm_palette)
        self.set_bpm_widget.setFixedWidth(50)
        self.control_layout.addWidget(self.set_bpm_widget)

        self.control_layout.addSpacing(50)

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
        self.audio_selection.addItems(input_devices)
        self.audio_selection.currentIndexChanged.connect(self.audio_selection_changed)
        self.device_layout.addWidget(self.audio_selection)

        self.layout.addLayout(self.device_layout)

        self.central.setLayout(self.layout)

    def set_bpm(self, bpm):
        if self.lock_checkbox.isChecked():
            return

        if self.limit_checkbox.isChecked():
            while bpm < self.lower_bpm_limit:
                bpm = bpm * 2.0
            while bpm > self.upper_bpm_limit:
                bpm = bpm / 2.0
        self.video_widget.set_bpm(bpm)
        self.set_bpm_widget.setText("{:.1f}".format(self.video_widget.old_bpm))

    def update_bpm_manually(self):
        bpm = self.set_bpm_widget.text()
        try:
            bpm = float(bpm)
            if bpm < 1.0:
                raise ValueError
        except ValueError:
            return
        self.video_widget.set_bpm(bpm)
        self.set_bpm_widget.setText("{:.1f}".format(self.video_widget.old_bpm))

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

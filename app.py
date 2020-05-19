import json

from PySide2.QtWidgets import QApplication

from mainwindow import MainWindow
from audio_device import AudioDevice
from bpm_helper import BPMQt, BPMmp

class App(QApplication):
    """Main application class for combining audio analysis with UI.

    Gives the option to choose between Qt's QThreads and Python's own
    multiprocessing module for heavy audio data calculation. QThreads should be
    better on computers with faster CPU cores but smaller number of them, while
    multiprocessing should be better if there are more CPU cores.

    Essentia accepts 2 different algorithms. "multifeature" is more accurate
    and gives confidence level but is slower. "degara" is much faster but
    doesn't give confidence level.
    """
    def __init__(self):
        super().__init__()
        # default values
        self.use_qt_thread = False
        self.rhythm_algorithm = "multifeature"
        self.default_device_name = ""
        self.show_video_preview = True
        self.video_loop_bpm = 60
        self.video_update_skip_ms = 100

        self.read_config()

        self.setApplicationName("Gandalf Enjoys Music")

        self.window = MainWindow(self.show_video_preview,
                                 self.video_loop_bpm,
                                 self.video_update_skip_ms)
        self.window.show()

        self.bpm_set_fun = self.window.set_bpm

        self.audio = AudioDevice(self.default_device_name)

        if self.use_qt_thread:
            self.bpm_extractor = BPMQt(self.bpm_set_fun,
                                       algorithm=self.rhythm_algorithm)
        else:
            self.bpm_extractor = BPMmp(self.bpm_set_fun,
                                       algorithm=self.rhythm_algorithm)

        self.audio.data_ready.connect(self.bpm_extractor.start_bpm_calculation)

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

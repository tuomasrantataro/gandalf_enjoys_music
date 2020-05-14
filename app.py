"""Main app combining GUI and audio feature extraction."""
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
    use_qt_thread = True
    rhythm_algorithm = "multifeature"

    def __init__(self):
        super().__init__()
        self.setApplicationName("Gandalf Enjoys Music")

        self.window = MainWindow()
        self.window.show()

        self.bpm_set_fun = self.window.set_bpm

        self.audio = AudioDevice()

        if self.use_qt_thread:
            self.bpm_extractor = BPMQt(self.bpm_set_fun,
                                       algorithm=self.rhythm_algorithm)
        else:
            self.bpm_extractor = BPMmp(self.bpm_set_fun, algorithm=self.rhythm_algorithm)

        self.audio.data_ready.connect(self.bpm_extractor.start_bpm_calculation)

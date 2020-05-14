"""Main app combining GUI and audio feature extraction."""

import multiprocessing as mp

from PySide2.QtCore import Signal, QThread, QObject, Slot, QTimer
from PySide2.QtWidgets import QApplication

import essentia
import essentia.standard

from mainwindow import MainWindow
from audio_device import AudioDevice

def bpm_helper(queue, audio, method="multifeature"):
    """Find Beats per Minute from audio data.

    Choose rhythm extractor algorithm based on CPU resources available.
    Multifeature is more accurate but slower. Degara also has no confidence
    level calculation (always returns 0), so remove it if using that algorithm.
    """
    min_tempo = 40
    max_tempo = 150
    if method == "degara":
        rhythm_extractor = essentia.standard.RhythmExtractor2013(
            method="degara", minTempo=min_tempo, maxTempo=max_tempo)
        bpm, _, _, _, _ = rhythm_extractor(audio)
        print("BPM:", bpm)
        queue.put(bpm)

    else:
        rhythm_extractor = essentia.standard.RhythmExtractor2013(
            method="multifeature", minTempo=min_tempo, maxTempo=max_tempo)
        bpm, _, beats_confidence, _, _ = rhythm_extractor(audio)
        print("BPM: {} Confidence: {}".format(bpm, beats_confidence))
        if beats_confidence > 2.5:
            queue.put(bpm)
        else:
            queue.put(-1)

    return 0

class Worker(QObject):
    """Worker thread for calculating BPM with QThread.

    Parameters:
        audio (numpy.ndarray): A few seconds of audio data in signed int format.

    Emits:
        bpm(float): Emitted if found beats per minute with a high enough
                    confidence level.
        finished(): Emitted always when calculation is done.
    """
    finished = Signal()
    bpm = Signal(float)
    min_tempo = 40
    max_tempo = 150

    def __init__(self, audio, method="multifeature"):
        super().__init__()
        self.audio = audio
        self.method = method

    Slot()
    def extract_bpm(self):
        """Find Beats per Minute from audio data."""
        #audio = self.audio
        if self.method == "degara":
            rhythm_extractor = essentia.standard.RhythmExtractor2013(
                method="degara",
                minTempo=self.min_tempo,
                maxTempo=self.max_tempo)
            bpm, _, _, _, _ = rhythm_extractor(self.audio)
            self.bpm.emit(bpm)
        else:
            rhythm_extractor = essentia.standard.RhythmExtractor2013(
                method="multifeature",
                minTempo=self.min_tempo,
                maxTempo=self.max_tempo)
            bpm, _, beats_confidence, _, _ = rhythm_extractor(self.audio)
            print("BPM: {} Confidence: {}".format(bpm, beats_confidence))
            if beats_confidence > 2.5:
                self.bpm.emit(bpm)

        self.finished.emit()
        return 0

class App(QApplication):
    """Main application class for combining audio analysis with UI.

    Gives the option to choose between Qt's QThreads and Python's own
    multiprocessing module for heavy audio data calculation. QThreads should be
    better on computers with faster CPU cores but smaller number of them, while
    multiprocessing should be better if there are more CPU cores.

    Essentia accepts 2 different algorithms. "multifeature" is more accurate and
    gives confidence level but is slower. "degara" is much faster but doesn't
    give confidence level.
    """
    use_qt_thread = True
    essentia_rhythm_algorithm = "multifeature"
    bpm = Signal(float)

    def __init__(self):
        super().__init__()
        self.setApplicationName("Gandalf Enjoys Music")

        self.window = MainWindow()
        self.window.show()

        self.audio = AudioDevice()

        if self.use_qt_thread:
            self.worker = None
            self.worker_thread = None
            self.audio.data_ready.connect(self.start_bpm_calculation_qt)

        else:
            self.queue = mp.Queue()
            self.process = None
            self.audio.data_ready.connect(self.start_bpm_calculation_mp)

            self.bpm_timer = QTimer()
            self.bpm_timer.setInterval(1000)
            self.bpm_timer.timeout.connect(self.update_bpm_mp)
            self.bpm_timer.start()

    def start_bpm_calculation_qt(self, audio):
        """Set up thread and start BPM calculation."""
        self.worker = Worker(audio, self.essentia_rhythm_algorithm)
        self.worker_thread = QThread()
        self.worker_thread.started.connect(self.worker.extract_bpm)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.bpm.connect(self.update_bpm_qt)
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.start()

    def start_bpm_calculation_mp(self, audio):
        """Start new process to calculate BPM."""
        self.process = mp.Process(target=bpm_helper,
                                  args=(self.queue,
                                        audio,
                                        self.essentia_rhythm_algorithm))
        self.process.start()

    def update_bpm_qt(self, bpm):
        """Update BPM for changing Gandalf gif's playback speed."""
        if 0 < bpm < 300:
            self.window.set_bpm(bpm)

    def update_bpm_mp(self):
        """Update BPM for changing Gandalf gif's playback speed."""
        try:
            bpm = self.queue.get(False)
            self.process.join()
            if 0 < bpm < 300:   # essentia outputs ~738bpm when nothing plays.
                self.window.set_bpm(bpm)
        except mp.queues.Empty:
            pass

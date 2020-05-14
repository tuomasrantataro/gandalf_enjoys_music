"""This module includes two different ways for calculating tempo (BPM)"""
import multiprocessing as mp

import essentia
import essentia.standard

from PySide2.QtCore import Signal, Slot, QThread, QObject, QTimer

class BPMWorkerQt(QObject):
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

class BPMQt():
    """Calculate BPM using a QThread."""
    def __init__(self, bpm_set_fun, algorithm="multifeature"):
        self.bpm_set_fun = bpm_set_fun
        self.essentia_rhythm_algorithm = algorithm
        self.worker = None
        self.worker_thread = None

    def start_bpm_calculation(self, audio):
        """Set up thread and start BPM calculation."""
        self.worker = BPMWorkerQt(audio, self.essentia_rhythm_algorithm)
        self.worker_thread = QThread()
        self.worker_thread.started.connect(self.worker.extract_bpm)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.bpm.connect(self.update_bpm)
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.start()

    def update_bpm(self, bpm):
        """Update BPM for changing Gandalf gif's playback speed."""
        if 0 < bpm < 300:
            self.bpm_set_fun(bpm)

class BPMmp():
    """Calculate BPM using Python's native multiprocessing module."""
    def __init__(self, bpm_set_fun, algorithm="multifeature"):
        self.bpm_set_fun = bpm_set_fun
        self.essentia_rhythm_algorithm = algorithm

        self.queue = mp.Queue()
        self.process = None

        self.bpm_timer = QTimer()
        self.bpm_timer.setInterval(1000)
        self.bpm_timer.timeout.connect(self.update_bpm)
        self.bpm_timer.start()


    def start_bpm_calculation(self, audio):
        """Start new process to calculate BPM."""
        self.process = mp.Process(target=self.bpm_helper,
                                  args=(self.queue,
                                        audio,
                                        self.essentia_rhythm_algorithm))
        self.process.start()

    def update_bpm(self):
        """Update BPM for changing Gandalf gif's playback speed."""
        try:
            bpm = self.queue.get(False)
            self.process.join()
            if 0 < bpm < 300:
                self.bpm_set_fun(bpm)
        except mp.queues.Empty:
            pass

    @staticmethod
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

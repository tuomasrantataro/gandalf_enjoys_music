import numpy as np

from PySide2.QtCore import QObject, Signal, Slot, QTimer
from PySide2.QtMultimedia import QAudio, QAudioDeviceInfo, QAudioFormat, QAudioInput

from audio_data_handler import AudioDataHandler

class AudioDevice(QObject):
    """Class for storing computer's audio system information."""
    data_ready = Signal(np.ndarray)
    def __init__(self, default_device_name):
        super().__init__()
        self.default_device_name = default_device_name
        self._pull_timer = QTimer()
        self._pull_timer.setInterval(3000)
        self._pull_timer.timeout.connect(self.write_to_buffer)

        self._audio_input = None
        self._input = None
        self._audio_data_handler = None

        devices = QAudioDeviceInfo.availableDevices(QAudio.AudioInput)
        self._device = None
        self.monitors = []

        for item in devices:
            dev_name = item.deviceName()
            if dev_name.endswith(".monitor"):
                self.monitors.append(item)
            if item.deviceName() == self.default_device_name:
                self._device = item
        if not self._device:
            try:
                self._device = self.monitors[0]
            except IndexError:
                self._device = QAudioDeviceInfo.defaultInputDevice()

        self.initialize_audio()

        self.start_audio()

    def initialize_audio(self):
        """Set up parameters for audio recording."""
        self._format = QAudioFormat()
        self._format.setSampleRate(44100)
        self._format.setChannelCount(1)
        self._format.setSampleSize(8)
        self._format.setSampleType(QAudioFormat.UnSignedInt)
        self._format.setByteOrder(QAudioFormat.LittleEndian)
        self._format.setCodec("audio/pcm")

        device_info = QAudioDeviceInfo(self._device)
        if not device_info.isFormatSupported(self._format):
            print("Default format not supported - trying to use nearest.")
            self._format = device_info.nearestFormat(self._format)

        self._audio_data_handler = AudioDataHandler(self._format)

        self._audio_input = QAudioInput(self._device, self._format)
        self._audio_data_handler.data_ready.connect(self.data_ready)

    def start_audio(self):
        """Start running all audio objects."""
        self._audio_data_handler.start()
        self._audio_input.start(self._audio_data_handler)
        self._input = self._audio_input.start()
        self._pull_timer.start()

    stateMap = {
        QAudio.ActiveState: "ActiveState",
        QAudio.SuspendedState: "SuspendedState",
        QAudio.StoppedState: "StoppedState",
        QAudio.IdleState: "IdleState"
    }

    @Slot()
    def write_to_buffer(self):
        """Write data to buffer for later analysis."""
        len_ = self._audio_input.bytesReady()
        if len_ > 0:
            self._audio_data_handler.writeData(self._input.readAll(), len_)

import numpy as np

from PySide2.QtCore import QObject, Signal, Slot, QTimer
from PySide2.QtMultimedia import QAudio, QAudioDeviceInfo, QAudioFormat, QAudioInput

from audio_data_handler import AudioDataHandler

class AudioDevice(QObject):
    """Class for storing computer's audio system information."""
    data_ready = Signal(np.ndarray)
    audio_inputs = Signal(object)
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
            if self.default_device_name and self.default_device_name == item.deviceName():
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

    def get_input_devices(self):
        devices = []
        if self._device:
            devices.append(self._device)
        for item in self.monitors:
            if item.deviceName() not in [x.deviceName() for x in devices]:
                devices.append(item)
        system_default = QAudioDeviceInfo.defaultInputDevice()
        if system_default not in [x.deviceName() for x in devices]:
            devices.append(system_default)
        return devices

    def get_input_device_names(self):
        devices = self.get_input_devices()
        names = [x.deviceName() for x in devices]
        return names

    @Slot(str)
    def change_audio_input(self, input_name):
        input_devices = self.monitors
        input_devices.append(QAudioDeviceInfo.defaultInputDevice())
        for i in range (len(input_devices)):
            if input_devices[i].deviceName() == input_name:
                self._device = input_devices[i]
                self.initialize_audio()
                self.start_audio()
                break

    @Slot()
    def write_to_buffer(self):
        """Write data to buffer for later analysis."""
        len_ = self._audio_input.bytesReady()
        if len_ > 0:
            self._audio_data_handler.writeData(self._input.readAll(), len_)

import numpy as np
assert np

from PySide2.QtCore import Signal, Slot, QIODevice, QByteArray

class AudioDataHandler(QIODevice):
    """Class for storing incoming audio data in a buffer for later analysis.

    _buffer_size determines how much audio data is used when trying to find
    beats per minute (BPM) value. The value set has been found experimentally
    to give accurate BPM values without too much delay when BPM changes.

    With current settings (44100Hz, 8bit uint), the buffe fills with 44100B/s.
    Therefore, buffer of 350000 holds a bit more than 7 seconds of audio data.
    """
    data_ready = Signal(np.ndarray)
    _buffer_size = 350000

    def __init__(self, format_):
        super().__init__()

        self._buffer = QByteArray()
        self._format = format_
        self.data = None

    def start(self):
        self.open(QIODevice.WriteOnly)

    def stop(self):
        self.close()

    @Slot(QByteArray, int)
    def writeData(self, new_data, len_):
        """Write new data to buffer.

        Keeps buffer at constant size.

        Emits:
            data_ready(numpy.ndarray): When new data is written, emit all data
                                       for later analysis.
        """
        self._buffer.append(new_data.data())

        data = self._buffer.data()
        self._buffer = self._buffer.right(self._buffer_size)

        data_array = np.frombuffer(data, dtype="uint8")
        data_array = data_array.astype("int")
        self.data_ready.emit(data_array)

        return len_

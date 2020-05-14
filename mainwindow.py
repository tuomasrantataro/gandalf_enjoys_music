from PySide2.QtCore import Slot
from PySide2.QtWidgets import QMainWindow, QLabel
from PySide2.QtGui import QMovie

#from audio_device import AudioDevice

class MainWindow(QMainWindow):
    """Display nodding Gandalf loop."""
    def __init__(self):
        super().__init__()
        self.gandalf_gif = None
        self.gandalf_label = None
        self.initialize_video()

        self.show()

    def initialize_video(self):
        """Set up showing the gandalf gif

        To generate gif, run ffmpeg with these parameters:
        ffmpeg -ss 0.0 -t 1.0 -i gandalf.mp4 -filter_complex "[0:v] split [a][b];[a] palettegen [p];[b][p] paletteuse" gandalf.gif

        Details of the gif:
            19 frames, 23.98 fps
            -> (19/23.98) ~= 0.79s loop
            -> 60/0.79s = 75.263... bpm for normal playback speed

            " 71.94

        """
        self.gandalf_default_bpm = 71.94

        self.gandalf_gif = QMovie("./resources/gandalf.gif")
        self.gandalf_gif.start()

        self.gandalf_label = QLabel()
        self.gandalf_label.setMovie(self.gandalf_gif)

        self.setCentralWidget(self.gandalf_label)

        self.set_bpm(self.gandalf_default_bpm)

    @Slot(float)
    def set_bpm(self, bpm):
        """Update playback speed for Gandalf gif."""
        print("BPM updated:", bpm)
        gandalf_speed = 100 * bpm/self.gandalf_default_bpm
        self.gandalf_gif.setSpeed(gandalf_speed)

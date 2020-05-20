"""Program to make Gandalf enjoy music with you.

This program monitors computer's sound output and matches video loop of nodding
Gandalf to tempo extracted from audio stream.

Qt is used for audio device handling and video output, but tempo analysis is
done using Essentia library.

Author: Tuomas Rantataro
Date: 21.5.2020
"""

import sys

from PySide2.QtWidgets import QApplication

from mainwindow import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Gandalf Enjoys Music")

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

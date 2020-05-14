"""Program to make Gandalf enjoy music with out.

This program monitors computer's sound output and matches gif of nodding
Gandalf to beats per minute (BPM) extracted from audio stream.

Qt is used for audio device handling and video output, but BPM extraction is
done using Essentia library.

Author: Tuomas Rantataro
Date: 13.5.2020
"""

import sys

from app import App

def main():
    app = App()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

# gandalf_enjoys_music
Show Gandalf nodding according to music tempo

Gandalf is a huge fan of the Epic Sax Guy

(https://www.youtube.com/watch?v=G1IbRujko-A)

[<img src="https://img.youtube.com/vi/G1IbRujko-A/maxresdefault.jpg" width="50%">](https://youtu.be/G1IbRujko-A)

What if Gandalf could enjoy other music, too?

This program analyzes audio output to find tempo of the music which is currently playing. After finding tempo, the program adjusts the Gandalf nodding loop's playback speed accordingly.

## Requirements
Python packages:
- PySide2
- Essentia
- pydbus
- vext
- vext.gi

Linux packages:
- python3-gi
- ffmpeg

## Creating video from one loop
Qt's Media player does not allow seamless switching between videos, meaning that when a video ends and the next one starts, there will be a small gap in playback. This is mitigated by creating a long video of the loop repeating.

To create a long file from your loop, put it in `resources` -folder as `video.mp4` and run `generate_video.sh`. The script prints tempo (BPM) of the video which should be updated to `config.JSON`.

The script has option to interpolate higher fps movie for better slow motion playback when music BPM is lower than video's. However, playing high-fps videos at high playback speed can be too heavy for slow computers so it is disabled by default.
#!/bin/bash

if ! [ -x "$(command -v ffmpeg)" ]; then
    echo "Error: ffmpeg not installed."
    echo "Please install ffmpeg and try again."
    exit 1
fi

# remove previous files if present
rm -f video_long.mp4
rm -f video_short.mp4

# remove audio track
ffmpeg -nostats -loglevel 0 -i video.mp4 -c copy -an video_short.mp4

interpolate=false
# Interpolate to higher fps video. The interpolate video may cause problems with fast playback on slow computers.
if [ $interpolate = true ]; then
    mv video_short.mp4 video_short_.mp4
    ffmpeg -i video_short_.mp4 -filter "minterpolate='mi_mode=mci:mc_mode=aobmc:vsbmc=1'" video_short.mp4
    rm -f video_short_.mp4
fi

# multiply the original file until its length is over 1 hour or size over 1 GB (or it has been double 16 times)
counter=0
duration=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 video.mp4)
size=$(stat -c%s video.mp4)

echo "file video_short.mp4" > list.txt
echo "file video_short.mp4" >> list.txt
while [ $counter -lt 16 ] && (($(echo "$duration < 3600" |bc -l))) && [ $size -lt 1000000000 ]; do
    let counter+=1
    ffmpeg -nostats -loglevel 0 -f concat -safe 0 -i list.txt -c copy video_long.mp4
    mv video_long.mp4 video_short.mp4
    size=$(stat -c%s video_short.mp4)
    duration=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 video_short.mp4)
    echo "Doubling $counter, duration: $duration seconds, size: $size bytes."
done

echo ""
echo "Final file size: $size bytes"
echo "Final video length: $duration seconds"

bpm=$(echo "60/($duration/2^$counter)" |bc -l)
echo ""
echo "Loop BPM: $bpm"
mv video_short.mp4 video_long.mp4
rm -f list.txt
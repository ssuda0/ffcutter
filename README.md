
# ffCutter
ffCutter is  video cutter program. </br>
This program cut video frames and data files you want to cut</br>
</br>
</br>

## Usage
__1.__ execute program</br>
Click ffcutter.exe file</br>

__2.__ load video file</br>
Click open file button and load a video file</br>
or</br>
Load a text file containing informations about videos and frames you want to cut</br>
If you load text file, ffcutter automatically performs step 3 and step 4.</br></br>

__3.__ set scenes you want to cut</br>
Drop an anchor by pressing the z key</br></br>

__4.__ save the scenes</br>
Click run button </br></br>

## Form Of Text File
__form of text file__</br>
input video directory | output video directory | start framenum | end framenum</br></br>
if you give a input video directory as a video file, ffcutter will cut only video file
if you give a input video directory as a path, ffcutter will cut video file and data files
__example of text file__</br>
.\data1\Test_1.mp4 .\video_light 3 5</br>
.\data3\Test_3.mp4 .\video_darkness 1 2</br>
.\data3 .\video_data_darkness 10 13</br></br>


## Manual
__Usage__</br>
    ffcutter</br>
    ffcutter -h | --help</br></br>

__Examples__</br>
    ffcutter</br></br>

__GUI keys__</br>
GUI keys:
space - Play/pause.
arrows - Step frames.
ctrl + arrows - Step seconds.
alt + arrows - Jump anchors.
up/down arrows - Step 5%.

z - Put anchor on the current playback position.
x - Remove highlighted anchor.

h - Print this help message to the terminal.
i - Print input file information to the terminal.

ctrl + o - Open its directory.

f - Input frame start/end shift which will be applied to all segments during encoding / stream copy.

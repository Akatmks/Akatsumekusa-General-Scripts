## TimingOffset.py

Detect whether Web and BD sources align based on video keyframe \(It's suprisingly effective!\).  

<img src="https://github.com/user-attachments/assets/154476e1-8ea6-41ba-b033-702b731827c4" alt="TimingOffset.py Function Preview" width="564" />

### Installing TimingOffset.py

1. Install [VapourSynth](https://www.vapoursynth.com/) and install [lsmas](https://vsdb.top/plugins/lsmas) to the VapourSynth.  
2. Install dependencies into the python the VapourSynth binds to:  
   ```sh
   python3 -m pip install numpy scikit-learn
   ```
3. Download [TimingOffset.py](https://github.com/Akatmks/Akatsumekusa-General-Scripts/blob/master/TimingOffset/TimingOffset.py).

### Using TimingOffset.py

```sh
python3 "TimingOffset.py" "left.mkv" "right.mkv"
```
Replace `left.mkv` and `right.mkv` with the files you want to compare. If you are comparing Web sources against BD sources, put the Web sources on the left and BD sources on the right. After running the command, TimingOffset.py will analyse the two files (or folders) and print the report to the terminal.  

Both left and right parameters support:  
- Video files,  
- lwi files generated by lsmas (`.lwi`),  
- Keyframe format files (files starting with `# keyframe format v1`), and  
- Folders containing these three types of files.

Yes! it supports comparing between entire folders. It will recognise episode numbers from filename, and most likely you won't need to rename or move any files inside the folders for it to work.  
```sh
python3 "TimingOffset.py" "TV Batch Folder" "BD Encode Folder"
```

Note that in order for TimingOffset.py to work, the video files or lwi files fed to TimingOffset.py must be encoded with variable GOP. Most encodes from encoders or subtitle groups have variable GOP, but most sources directly from streaming platforms don't.  

On another note, there is an existing program called [Sushi](https://github.com/tp7/Sushi) from [Victor Efimov](https://github.com/tp7) that can compare between audio and recognise timing offsets. Shifting subtitles based solely on audio isn't as reliable, or even desirable as shifting based on video. However, it may be a good idea to shift the dialogue based on audio, and then resnap to video scene changes. Thanks to natsuakge for recommending Sushi as an alternative.  

## nyaa_notify.py \[Windows only\]

Are you waiting for an episode on Nyaa but you have no idea when it will be out?  
nyaa_notify.py is a script that helps you watch Nyaa and sends a desktop notification to you once a new episode is available.  

```sh
# Download the script
wget "https://raw.githubusercontent.com/Akatmks/Akatsumekusa-General-Scripts/master/nyaa_notify/nyaa_notify.py"

# Install the requirments using pip
python3 -m pip install -r "https://raw.githubusercontent.com/Akatmks/Akatsumekusa-General-Scripts/master/nyaa_notify/requirements.txt"

# Run the script help
./nyaa_notify.py --help
```

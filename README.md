## TimingOffset.py

Detect whether Web and BD sources align based on video keyframe \(It's suprisingly effective!\).  

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
- lwi files generated by lsmas (`*.lwi`),  
- Keyframe format files (files starting with `# keyframe format v1`), and  
- Folders containing these three types of files.

Yes! it supports comparing between entire folders:
```sh
python3 "TimingOffset.py" "TV Batch Folder" "BD Encode Folder"
```

Note that in order for TimingOffset.py to work, the video files or lwi files fed to TimingOffset.py must be encoded with variable GOP. Most encodes from encoders or subtitle groups has variable GOP, but most sources directly from streaming platforms doesn't.  

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

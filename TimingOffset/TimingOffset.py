#!/usr/bin/env python3

# TimingOffset
# Copyright (c) Akatsumekusa and contributors

# ---------------------------------------------------------------------
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ---------------------------------------------------------------------

import argparse
import os
from pathlib import Path
import platform
import math
import numpy as np
import re
from sklearn.preprocessing import StandardScaler
import tempfile
import typing

if platform.system() == "Windows":
    os.system("")

fps_num = 24000
fps_den = 1001
def print_frame(frame: int) -> str:
    return f"frame {frame} ({frame // (fps_num / fps_den * 60):02.0f}:{(frame % (fps_num / fps_den * 60)) // (fps_num / fps_den):02.0f})"
def print_offset(offset: int) -> str:
    if offset < 240:
        return f"{str(offset - 240)}f"
    else:
        return f"+{str(offset - 240)}f"

def get_keyframes_keyframe_format(f: typing.TextIO) -> list[int]:
    lines = []
    while True:
        try:
            line = f.readline()
        except UnicodeDecodeError:
            continue
        if not line:
            break

        if line.startswith("#") or line.startswith("fps"):
            continue

        line = line.rstrip()
        if line:
            try:
                line = int(line)
            except ValueError:
                continue
            lines.append(line)

    return lines

def get_keyframes_lwi(f: typing.TextIO) -> np.ndarray[bool]:
    lines = []
    while True:
        try:
            line = f.readline()
        except UnicodeDecodeError:
            continue
        if not line:
            break
        
        if line.startswith("Key="):
            lines.append(bool(int(line[4])))
        else:
            continue

    return np.array(lines, dtype=bool)

def get_keyframes_video(clip: Path) -> np.ndarray[bool]:
    from vapoursynth import core

    global fps_num
    global fps_den

    with tempfile.TemporaryDirectory(prefix="TimingOffset") as cache:
        cachefile = Path(cache).joinpath("TimingOffset.lwi")
        clip = core.lsmas.LWLibavSource(clip.as_posix(), cache=True, cachefile=cachefile.as_posix())
        print("\r\033[1A\033[K", end="")
        if clip.fps.numerator != 0 and clip.fps.denominator != 0:
            fps_num = clip.fps.numerator
            fps_den = clip.fps.denominator
        
        with cachefile.open("r", encoding="utf-8") as f:
            return get_keyframes_lwi(f)

def guess_filetype(path: Path) -> str:
    if path.stat().st_size > 16777216:
        return "binary"
    f = path.open("r", encoding="utf-8")
    try:
        line = f.readline()
        if line.startswith("# keyframe format") or line.startswith("fps"):
            f.close()
            return "keyframe_format"
        elif line.startswith("<LSMASHWorksIndexVersion"):
            f.close()
            return "lwi"
        else:
            f.close()
            return "binary"
    except UnicodeDecodeError:
        f.close()
        return "binary"

def get_keyframes(clip: Path) -> typing.Union[list[int], np.ndarray[bool]]:
    if clip.stat().st_size > 16777216:
        return get_keyframes_video(clip)
    f = clip.open("r", encoding="utf-8")
    try:
        line = f.readline()
        if line.startswith("# keyframe format") or line.startswith("fps"):
            result = get_keyframes_keyframe_format(f)
            f.close()
            return result
        elif line.startswith("<LSMASHWorksIndexVersion"):
            result = get_keyframes_lwi(f)
            f.close()
            return result
        else:
            f.close()
            return get_keyframes_video(clip)
    except UnicodeDecodeError:
        f.close()
        return get_keyframes_video(clip)

def inflate_keyframes_array(left: typing.Union[list[int], np.ndarray[bool]], right: typing.Union[list[int], np.ndarray[bool]]) -> tuple[np.ndarray[bool], np.ndarray[bool]]:
    if (left_type := isinstance(left, np.ndarray)) and (right_type := isinstance(right, np.ndarray)):
        return left, right
    elif left_type and (not right_type):
        new_right = np.zeros_like(left)
        for n in right:
            new_right[n] = True
        return left, new_right
    elif (not left_type) and right_type:
        new_left = np.zeros_like(right)
        for n in left:
            new_left[n] = True
        return new_left, right
    else:
        new_left = np.zeros(max(left[-1], right[-1]), dtype=bool)
        new_right = np.zeros_like(new_left)
        for n in left:
            new_left[n] = True
        for n in right:
            new_right[n] = True
        return new_left, new_right

this_is_likely_due_to = True

# Caller must assure that range was valid for both left and right array.
def guess_offset_range(left: np.ndarray[bool], right: np.ndarray[bool], range_: tuple[int]) -> typing.Optional[str]:
    global this_is_likely_due_to

    results = np.empty((481,), dtype=int)
    for iter in range(-240, 0):
        rl = max(range_[0] + iter, 0)
        rr = range_[1] + iter
        ll = range_[1] - (rr - rl)
        lr = range_[1]
        results[iter + 240] = np.count_nonzero(np.logical_and(left[ll:lr], right[rl:rr]))
    for iter in range(0, 241):
        rl = range_[0] + iter
        rr = min(range_[1] + iter, right.shape[0])
        ll = range_[0]
        lr = range_[0] + (rr - rl)
        results[iter + 240] = np.count_nonzero(np.logical_and(left[ll:lr], right[rl:rr]))

    clf = StandardScaler(copy=True)
    results = clf.fit_transform(results.reshape((-1, 1))).reshape((-1))
    results_significant = np.nonzero(results > 5)[0]
    
    if results_significant.shape[0] == 0:
        message = f"\033[31mCould not find a significant relevance between left and right clips between \033[1;33m{print_frame(range_[0])}\033[0;31m and \033[1;33m{print_frame(range_[1])}\033[0;31m.\033[0m\n"
        if (results_significant := np.nonzero(results > 4)[0]).shape[0] != 0:
            message += "Timing offset with high unit variance are:\n"
            for index in results_significant:
                message += f"\033[31m＊ \033[1;33m{print_offset(index).rjust(4)} \033[0mwith unit variance {results[index]:.3f}\033[31m.\033[0m\n"
        return message
    elif results_significant.shape[0] == 1:
        if results_significant[0] == 240:
            return None
        else:
            return f"\033[34mPossible \033[1;34m{print_offset(results_significant[0])}\033[0;34m offset between \033[1;34m{print_frame(range_[0])}\033[0;34m and \033[1;34m{print_frame(range_[1])}\033[0;34m \033[0mwith unit variance {results[results_significant[0]]:.3f}\033[34m.\033[0m\n"
    else:
        message = f"\033[34mMultiple possible offsets detected between \033[1;34m{print_frame(range_[0])}\033[0;34m and \033[1;34m{print_frame(range_[1])}\033[0;34m:\033[0m\n"
        for index in results_significant:
            message += f"\033[34m＊ \033[1;34m{print_offset(index).rjust(4)} \033[0mwith unit variance {results[index]:.3f}\033[34m.\033[0m\n"
        if this_is_likely_due_to:
            message += "This is likely due to changes in timing in the middle of the segment, for example, with earlier parts of the segment following one offset and later parts following another, or it might just be a coincident, especially in the case where one offset has very high unit variance while all other offsets have low unit variances.\n"
            this_is_likely_due_to = False
        else:
            message += "This may be due to changes in timing in the middle of the segment, or otherwise a coincident.\n"
        return message

def guess_offset(left: np.ndarray[bool], right: np.ndarray[bool]) -> typing.Optional[str]:
    a_message = None
    if (length := left.shape[0]) != right.shape[0]:
        length = min(left.shape[0], right.shape[0])
        if abs(left.shape[0] - right.shape[0]) > 72:
            a_message = "\033[33mLeft and right clips' length differs by more than 72 frames.\033[0m\n"
            a_message += f"Left clip has {str(left.shape[0])} frames.\n"
            a_message += f"Right clip has {str(right.shape[0])} frames.\n"
    
    b_message = None
    if length < 481:
        b_message = "\033[31mComparations on clips whose lengths are under 481 frames are not supported.\033[0m\n"
        b_message += str(left.shape)
    else:
        section_count = math.floor(length / 5754)
        section_length = math.floor(length / section_count)
        for i in range(section_count):
            if i < section_count - 1:
                return_message = guess_offset_range(left, right, (i * section_length, (i+1) * section_length))
            else:
                return_message = guess_offset_range(left, right, (i * section_length, length))
            if return_message:
                if b_message is None:
                    b_message = return_message
                else:
                    b_message += return_message

    if a_message and (not b_message):
        return a_message + "No timing differences were detected. Left and right clips are aligned.\n"
    elif (not a_message) and (not b_message):
        return None
    elif (not a_message) and b_message:
        return b_message
    else:
        return a_message + b_message

parser = argparse.ArgumentParser(prog="TimingOffset", description="Detect whether Web and BD sources align based on video keyframe")
parser.add_argument("left", type=Path, help="The clip to compare against. Supports video file, lwi file, keyframe format file, or directory containing such files (smart)")
parser.add_argument("right", type=Path, help="The clip to compare. Supports video file, lwi file, keyframe format file, or directory containing such files (smart)")
args = parser.parse_args()
left = args.left
right = args.right

file_match = re.compile(r"(?<![a-z0-9A-DF-Z])([0-9]{2}(?:\.[0-9])?)(?![a-uw-z0-9A-Z])")
messaged = False

def convert_path_to_list_of_files(path: Path):
    if path.is_file():
        return [path]

    elif path.is_dir():
        file_dict = {}
        for file in path.iterdir():
            if file.is_file() and (match := file_match.search(file.name)):
                file_key = float(match.group(1))
                if file_key in file_dict:
                    file_dict[file_key].append(file)
                else:
                    file_dict[file_key] = [file]

        file_list = []
        for key in sorted(file_dict):
            if len(file_dict[key]) == 1:
                file_list.append(file_dict[key][0])
            else:
                binary = None
                keyframe_format = None
                lwi = None
                for file in file_dict[key]:
                    if guess_filetype(file) == "binary":
                        if binary is None:
                            binary = file
                        else:
                            if file.stat().st_size > binary.stat().st_size:
                                binary = file
                    elif guess_filetype(file) == "lwi":
                        lwi = file
                    elif guess_filetype(file) == "keyframe_format":
                        keyframe_format = file
                    else:
                        raise ValueError

                if keyframe_format is not None:
                    file_list.append(keyframe_format)
                elif lwi is not None:
                    file_list.append(lwi)
                elif binary is not None:
                    file_list.append(binary)
                else:
                    raise ValueError
        return file_list
    else:
        raise ValueError(f"Path \"{path.as_posix()}\" is neither a file nor a directory.")

left = convert_path_to_list_of_files(left)
right = convert_path_to_list_of_files(right)

if len(left) != len(right):
    raise ValueError(f"Number of files in the left is different than number of files in the right.\n\tFiles in the left: {str([file.name for file in left])}\n\tFiles in the right: {str([file.name for file in right])}")
if len(left) == 0:
    raise ValueError(f"No file is recognised in either provided directories.")

for i in range(len(left)):
    if (match := file_match.search(left[i].name)):
        print(f"\033[1;37mComparing Episode {float(match.group(1)):02g}...\033[0m", end="\n")
    left_ = get_keyframes(left[i])
    right_ = get_keyframes(right[i])
    left_, right_ = inflate_keyframes_array(left_, right_)
    message = guess_offset(left_, right_)
    if message:
        messaged = True
        if match:
            print(f"\r\033[1A\033[K\033[1;37mOffsets in Episode {float(match.group(1)):02g} between left reference \033[0m\"{left[i].name}\"\033[1;37m and right target \033[0m\"{right[i].name}\"\033[1;37m:\033[0m", end="\n")
            print(message, end="")
        else:
            print(message, end="")
    else:
        if match:
            print("\r\033[1A\033[K", end="")

if not messaged:
    print("No timing differences were detected. Left and right clips are aligned.", end="\n")

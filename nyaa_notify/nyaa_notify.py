#!/usr/bin/env python3

# nyaa_notify.py
# Copyright (c) Akatsumekusa

# ---------------------------------------------------------------------
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# ---------------------------------------------------------------------

if True:
# +-------------------------------------------------------------------+
# | Welcome to nyaa_notify.py .                                       |
# | nyaa_notify.py is a script that watches Nyaa and notifies you     |
# | once a new episode is available.                                  |
# +-------------------------------------------------------------------+
# | nyaa_notify.py works by fetching Nyaa's RSS feed every few        |
# | minutes. You can set the feed for nyaa_notify.py to watch with    |
# | these steps:                                                      |
# | 1.   Open https://nyaa.si/ in your browser.                       |
# | 2.   Search for the items you are looking for in the search bar,  |
# |      for example, „SubsPlease Wonder Egg Priority“.               |
# | 3.   Right click the „RSS“ button on the navigation bar, select   |
# |      „Copy Link“.                                                 |
# | 4.   Paste the link in the feed field below. The link should be   |
# |      something like                                               |
# |      "https://nyaa.si/?page=rss&q=SubsPlease+Wonder+Egg+Priority&c=0_0&f=0".
    feed = ""
# | You can also set how often nyaa_notify.py should look for new     |
# | updates in the feed in the update_interval field below in         |
# | minutes. Akatsumekusa's default value is 3, or 3 minutes.         |
    update_interval = 3
# | Note that Nyaa often has a delay between an item is published     |
# | and it is being updated to the RSS feed. As an estimation, you    |
# | can expect to receive a notification within (update_interval + 5) |
# | minutes after an item is published.                               |
# +-------------------------------------------------------------------+
# | Sometimes you may not have realised that an item is already       |
# | published. In order to prevent that, nyaa_notify.py can trace     |
# | backwards to check the items published before.                    |
# | You can set how long should nyaa_notify.py trace backwards in the |
# | traceback field below in minutes. Akatsumekusa's default value is |
# | 720, or exactly 12 hours.                                         |
    traceback = 720
# +-------------------------------------------------------------------+
# | Sometimes you may not be able to be in front of your computer at  |
# | all times. In case you miss the notification, nyaa_notify.py      |
# | could try to send another notification next time it updates.      |
# | Set the times you want to be notified in the pings field below.   |
# | Akatsumekusa personally sets this value to 2 but the default      |
# | value here in nyaa_notify.py is 1.                                |
    pings = 1
# +-------------------------------------------------------------------+
# | These config values could be overwritten in cli. Use              |
# | `./nyaa_notify.py --help` for more information.                   |
# +-------------------------------------------------------------------+

import argparse
from cjkwrap import cjkslices
from datetime import datetime, timedelta
from feedparser import parse
import os
import re
import shutil
import signal
import sys
import time
import win10toast

toast = win10toast.ToastNotifier()
            
pls_exit = False
_times = 0
def interrupt(sig = None, frame = None, times: int = -1) -> None:
    global pls_exit, _times
    if times != -1:
        _times = times
    if _times == 0:
        print("[nyaa_notify] Exiting gracefully...", flush=True)
        _times += 1
        pls_exit = True
    elif _times == 1:
        print("[nyaa_notify] Exiting...", flush=True)
        _times += 1
        sys.exit()
    elif _times == -2:
        _times = 2
        sys.exit()
    else:
        print("[nyaa_notify] Force exiting...", flush=True)
        os._exit(-1)

def nyaa_notify() -> None:
    parser = argparse.ArgumentParser(prog="nyaa_notify.py",
                                     epilog="If you want a slightly longer description for each arguments, or you just don't want to type \
                                             the same url every times, or you prefer to directly double click the py file to run, open \
                                             nyaa_notify.py in a text editor and head to around line 21.")
    if feed:
        parser.add_argument("url", help="URL for the RSS feed (set in nyaa_notify.py: \"" + feed + "\")", nargs="?", default=feed)
    else:
        parser.add_argument("url", help="URL for the RSS feed")
    parser.add_argument("-i", "--interval", help="set the update interval in minutes (default: " + str(update_interval * 60) + ")", type=float, default=update_interval)
    parser.add_argument("-t", "--traceback", help="set traceback in minutes (default: " + str(traceback) + ")", type=float, default=traceback)
    parser.add_argument("-p", "--pings", help="set the number of notifications you want to receive for each entry (default: " + str(pings) + ")", type=int, default=pings)
    
    if pls_exit:
        return
    args = parser.parse_args()

    rss(args.url, args.interval * 60, args.traceback, args.pings)

def rss(rss_url: str, interval: float, traceback: float, pings: int) -> None:
    traceback = datetime.now() - timedelta(minutes=traceback)
    if pls_exit:
        return
    rss_notify(rss_url, traceback, datetime.now(), pings)

    while True:
        signal.signal(signal.SIGINT, signal.default_int_handler)
        try:
            if pls_exit:
                return
            time.sleep(interval)
        except KeyboardInterrupt:
            interrupt(times=-2)
        signal.signal(signal.SIGINT, interrupt)

        rss_notify(rss_url,
                   datetime.now() - timedelta(minutes=30) if datetime.now() - timedelta(minutes=30) > traceback else traceback,
                   datetime.now(),
                   pings)

notified_entries = {}
# It is always confusing what before and after means. If we plot these
# two variables in a timeline:
# notify_after ----> entries to notify ----> notify_before ----> year 2029
# assuming you won't be using this script as far into the future as
# 2029 (
def rss_notify(rss_url: str, notify_after: datetime, notify_before: datetime, pings: int) -> None:
    # notified_entries[entry_title: str] = [entry_url: str, ping: int]
    global notified_entries

    signal.signal(signal.SIGINT, signal.default_int_handler)
    try:
        if pls_exit:
            return
        feed = parse(rss_url)
    except KeyboardInterrupt:
        interrupt(times = 2)
        if pls_exit:
            return
    signal.signal(signal.SIGINT, interrupt)

    for entry in feed.entries:
        if notify_after <= datetime(entry.published_parsed[0], entry.published_parsed[1], entry.published_parsed[2],
                                    entry.published_parsed[3], entry.published_parsed[4], entry.published_parsed[5]
                                    ) <= notify_before:
            if entry.title not in notified_entries:
                entry_url = ""
                if hasattr(entry, "summary"):
                    entry_url = re.search("(?<=\\\")(?=http\\:\\/\\/|https\\:\\/\\/).*?(?=\\\")", entry.summary).group(0)
                if not entry_url and hasattr(entry, "link"):
                    entry_url = entry.link
                if not entry_url:
                    entry_url = ""
                notified_entries[entry.title] = [entry_url, 0]
    
    if pls_exit:
        return
    print_notify(notified_entries)
    if pls_exit:
        return
    toast_notify_and_update_dict(notified_entries, pings)

def print_notify(notify_entries: dict[list[str, int]]) -> None:
    feed_updated_showed = False
    
    for entry_title in notify_entries:
        if notify_entries[entry_title][1] == 0:
            if notify_entries[entry_title][0]:
                if not feed_updated_showed:
                    print("[nyaa_notify] Feed updated:")
                    print("[nyaa_notify] " + "-" * (shutil.get_terminal_size((80, 24))[0] - 14))
                    feed_updated_showed = True
                print("[nyaa_notify] \033[1m" +
                      "\033[0m\n[nyaa_notify] \033[1m".join(cjk_warp(entry_title, shutil.get_terminal_size((80, 24))[0] - 14)) +
                      "\033[0m")
                print("[nyaa_notify] " + 
                      "\n[nyaa_notify] ".join(cjk_warp(notify_entries[entry_title][0], shutil.get_terminal_size((80, 24))[0] - 14)))
                print("[nyaa_notify] " + "-" * (shutil.get_terminal_size((80, 24))[0] - 14), flush=True)
            else:
                if not feed_updated_showed:
                    print("[nyaa_notify] Feed updated:")
                    feed_updated_showed = True
                print("[nyaa_notify] " + entry_title, flush=True)

def cjk_warp(text: str, len: int) -> list[str]:
    l = []
    while text:
        to_append, text = cjkslices(text, len)
        l.append(to_append)
        text = text.lstrip()
    return l

def toast_notify_and_update_dict(notify_entries: dict[list[str, int]], pings: int) -> None:
    for entry_title in notify_entries:
        if notify_entries[entry_title][1] < pings:
            # Toast notify
            for _ in range(3):
                try:
                    toast.show_toast("Feed updated", entry_title)
                except:
                    signal.signal(signal.SIGINT, signal.default_int_handler)
                    try:
                        if pls_exit:
                            break
                        time.sleep(1)
                    except KeyboardInterrupt:
                        interrupt()
                        break
                    signal.signal(signal.SIGINT, interrupt)
                else:
                    break

            # Update dict
            notify_entries[entry_title][1] += 1

        if pls_exit:
            return

if __name__ == "__main__":
    signal.signal(signal.SIGINT, interrupt)
    sys.stdout.reconfigure(encoding="utf-8")

    nyaa_notify()

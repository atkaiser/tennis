import argparse
import re
from pathlib import Path
from os import path
from os import remove
from collections import namedtuple, defaultdict
from video_tools import (
    get_movie_files,
    get_total_num_of_frames,
    get_video_fps,
    get_real_world_fps,
)
import sys

"""


author akaiser 2021-04-02
"""

FixInfo = namedtuple("Fix", ["frame_num", "old_cat", "new_cat"])


def main(video_dir, wrong_file_path):
    all_fixes = defaultdict(list)

    with open(wrong_file_path, "r") as f:
        for line in f:
            original_file_path, new_category = line.strip().split("---")
            original_file_path = Path(original_file_path)
            original_file_name = path.basename(str(original_file_path))
            original_category = path.basename(str(original_file_path.parent))
            search_obj = re.search(r'^(.*)-(\d+)\.jpg', original_file_name)
            video_name = search_obj.group(1)
            frame_num = int(search_obj.group(2))

            fix_info = FixInfo(frame_num, original_category, new_category)
            all_fixes[video_name].append(fix_info)

    for video in all_fixes:
        video_file_path = path.join(video_dir, video)

        video_name = path.splitext(video)[0]
        json_event_info = path.join(video_dir, video_name + ".json")

        with open(json_event_info) as f:
            all_actions = path.json.load(f)

        fixes = all_fixes[video]
        fixes.sort(key=lambda fix: fix.frame_num)

        val = input("For {} there are {} shots and {} fixes, do you want to keep the json? (d) for delete, (anything) "
                    "for keep")
        if val == "d":
            remove(json_event_info)
            continue

        for fix in fixes:
            action = find_closest_action(fix.frame_num, all_actions)
            


def find_closest_action(frame_num, all_actions):
    current_action = None
    current_distance = sys.maxint
    for action in all_actions:
        if action["start_frame"] <= frame_num <= action["end_frame"]:
            return action
        elif frame_num < action["start_frame"]:
            distance = action["start_frame"] - frame_num
        else:
            distance = frame_num - action["stop_frame"]
        if distance <= current_distance:
            current_action = action
            current_distance = distance
    return current_action

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create a label.json file for a video."
    )
    parser.add_argument(
        "--dir", help="Path to directory where all the training videos are."
    )
    parser.add_argument(
        "--wrong_file_path",
        help="Path to the file that has which data is incorrect",
    )
    args = parser.parse_args()

    main(args.dir, args.wrong_file_path)

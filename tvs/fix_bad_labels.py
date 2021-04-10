import argparse
import re
from pathlib import Path
from os import remove, replace, listdir
from os.path import splitext, basename, join, isfile
import json
import cv2
from collections import namedtuple, defaultdict
from video_tools import (
    get_video_fps,
    get_frame,
)
from curses import wrapper
from enum import Enum

"""
Script to fix the json file associated with videos.

author akaiser 2021-04-02
"""
FixInfo = namedtuple("Fix", ["frame_num", "old_cat", "new_cat"])


class FrameType(Enum):
    """
    Keep track of which type of frame is currently being looked at.
    """

    START = 0
    CONTACT = 1
    END = 2


def main_wrapper(stdscr):
    """
    Wrapper function around main so that curses can use the wrapper function
    to restore everything if there is an exception.
    """
    parser = argparse.ArgumentParser(
        description="Create a label.json file for a video."
    )
    parser.add_argument(
        "--dir", help="Path to directory where all the training videos are."
    )
    parser.add_argument(
        "--wrong_file_path",
        default="",
        help="Path to the file that has which data is incorrect",
    )
    args = parser.parse_args()
    stdscr.clear()
    main(stdscr, args.dir, args.wrong_file_path)
    cv2.destroyAllWindows()


def main(stdscr, video_dir, wrong_file_path):
    """
    Main loop that will accomplish the scripts purpose.
    """
    if isfile(video_dir):
        all_fixes = create_all_fixes_for_file(video_dir)
        video_dir = str(Path(video_dir).parent)
        video_passed_in = True
    else:
        video_passed_in = False
        all_fixes = populate_all_fixes(video_dir, wrong_file_path)

    for video in all_fixes:
        stdscr.clear()
        stdscr.refresh()
        stdscr.addstr("Working on {}\n".format(video))
        stdscr.refresh()
        video_file_path = join(video_dir, video)

        video_name = splitext(video)[0]
        json_event_info = join(video_dir, video_name + ".json")

        with open(json_event_info) as f:
            all_actions = json.load(f)

        fixes = all_fixes[video]
        fixes.sort(key=lambda f: f.frame_num)

        stdscr.addstr(
            2,
            0,
            "For {} there are {} shots and {} fixes, do you want to keep the"
            " json? (d) for delete, (anything) for keep".format(
                video_name, len(all_actions), len(fixes)
            ),
        )
        stdscr.refresh()
        val = stdscr.getkey()
        if val == "d":
            remove(json_event_info)
            continue

        stdscr.move(2, 0)
        stdscr.clrtoeol()
        stdscr.refresh()

        cap = cv2.VideoCapture(video_file_path)
        cv2.namedWindow("start", cv2.WINDOW_NORMAL)
        cv2.moveWindow("start", 0, 600)
        cv2.namedWindow("contact", cv2.WINDOW_NORMAL)
        cv2.moveWindow("contact", 640, 600)
        cv2.namedWindow("end", cv2.WINDOW_NORMAL)
        cv2.moveWindow("end", 1280, 600)
        cv2.namedWindow("fix", cv2.WINDOW_NORMAL)
        cv2.moveWindow("fix", 1280, 0)

        fixed_actions = set()
        for i, fix in enumerate(fixes):
            action_index, action = find_closest_action(fix.frame_num, all_actions)
            if action_index in fixed_actions:
                continue
            else:
                fixed_actions.add(action_index)
            start_frame_num = int(action["start_frame"])
            contact_frame_num = int(action["contact_frame"])
            end_frame_num = int(action["end_frame"])
            fix_frame_num = fix.frame_num

            current_type_to_edit = FrameType.START
            while True:
                text_to_display = "Showing fix {} of {}\n".format(i, len(fixes))
                text_to_display += "Was: {}\n".format(fix.old_cat)
                text_to_display += "Now: {}\n\n".format(fix.new_cat)
                text_to_display += "Fix frame    : {}\n\n".format(fix.frame_num)
                text_to_display += "Start frame  : {}\n".format(start_frame_num)
                text_to_display += "Contact frame: {}\n".format(contact_frame_num)
                text_to_display += "End frame    : {}\n\n".format(end_frame_num)
                text_to_display += "Currently editing: {}".format(
                    str(current_type_to_edit)
                )
                stdscr.move(2, 0)
                stdscr.clrtobot()
                stdscr.addstr(2, 0, text_to_display)
                stdscr.refresh()
                cv2.imshow(
                    "start", cv2.resize(get_frame(cap, start_frame_num), (640, 360))
                )
                cv2.imshow(
                    "contact", cv2.resize(get_frame(cap, contact_frame_num), (640, 360))
                )
                cv2.imshow("end", cv2.resize(get_frame(cap, end_frame_num), (640, 360)))
                cv2.imshow("fix", cv2.resize(get_frame(cap, fix_frame_num), (640, 360)))
                cv2.waitKey(1)
                pressed_key_value = stdscr.getkey()
                if pressed_key_value == "q":
                    return
                elif pressed_key_value == "n":
                    video_fps = get_video_fps(video_file_path)
                    action["start"] = start_frame_num / video_fps
                    action["contact"] = contact_frame_num / video_fps
                    action["end"] = end_frame_num / video_fps
                    action["start_frame"] = start_frame_num
                    action["contact_frame"] = contact_frame_num
                    action["end_frame"] = end_frame_num
                    break
                elif pressed_key_value == "s":
                    current_type_to_edit = FrameType.START
                elif pressed_key_value == "e":
                    current_type_to_edit = FrameType.END
                elif pressed_key_value == "c":
                    current_type_to_edit = FrameType.CONTACT
                elif pressed_key_value == "a":
                    if current_type_to_edit == FrameType.START:
                        start_frame_num -= 1
                    elif current_type_to_edit == FrameType.CONTACT:
                        contact_frame_num -= 1
                    else:
                        end_frame_num -= 1
                elif pressed_key_value == "d":
                    if current_type_to_edit == FrameType.START:
                        start_frame_num += 1
                    elif current_type_to_edit == FrameType.CONTACT:
                        contact_frame_num += 1
                    else:
                        end_frame_num += 1

            with open(json_event_info, "w") as f:
                f.write(json.dumps(all_actions, indent=2))

        if not video_passed_in:
            # Remove from wrong the lines just fixed
            with open(wrong_file_path, "r") as f:
                with open(wrong_file_path + ".tmp", "w") as new_wrong_file:
                    for line in f:
                        if splitext(video)[0] in line:
                            continue
                        else:
                            new_wrong_file.write(line)
            replace(wrong_file_path + ".tmp", wrong_file_path)


def create_all_fixes_for_file(video_path):
    """
    Create a bogus fixes dictionary for the video where there is a fix for each shot.
    This is used so that you can examine each shot in the video.
    """
    video_name = splitext(video_path)[0]
    json_event_info = video_name + ".json"
    with open(json_event_info) as f:
        actions = json.load(f)
    all_fixes = defaultdict(list)
    for action in actions:
        fix_info = FixInfo(int(action["contact_frame"]), "CONTACT", "CONTACT")
        all_fixes[basename(video_path)].append(fix_info)
    return all_fixes


def populate_all_fixes(video_dir, wrong_file_path):
    """
    Take in a wrong_file_path and generate a FixInfo for each line in the file.
    """
    all_fixes = defaultdict(list)
    all_files_in_video_dir = listdir(video_dir)

    with open(wrong_file_path, "r") as f:
        line_num = 0
        for line in f:
            original_file_path, new_category = line.strip().split("---")
            original_file_path = Path(original_file_path)
            original_file_name = basename(str(original_file_path))
            original_category = basename(str(original_file_path.parent))
            search_obj = re.search(r"^(.*)-(\d+)\.jpg", original_file_name)
            video_name_without_prefix = search_obj.group(1)
            frame_num = int(search_obj.group(2))

            video_name = ""
            for file_name in all_files_in_video_dir:
                if file_name.startswith(
                    video_name_without_prefix
                ) and not file_name.endswith("json"):
                    video_name = file_name
                    break

            if not video_name:
                continue

            fix_info = FixInfo(frame_num, original_category, new_category)
            all_fixes[video_name].append(fix_info)
            line_num += 1

    return all_fixes


def find_closest_action(frame_num, all_actions):
    """
    Find the closest action to a specific frame.
    """
    current_action = None
    current_action_index = -1
    current_distance = float("inf")
    for i, action in enumerate(all_actions):
        if action["start_frame"] <= frame_num <= action["end_frame"]:
            return i, action
        elif frame_num < action["start_frame"]:
            distance = action["start_frame"] - frame_num
        else:
            distance = frame_num - action["end_frame"]
        if distance <= current_distance:
            current_action = action
            current_action_index = i
            current_distance = distance
    return current_action_index, current_action


if __name__ == "__main__":
    wrapper(main_wrapper)

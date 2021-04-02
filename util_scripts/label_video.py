import cv2
import argparse
from enum import Enum
import time
from collections import namedtuple
import json
from os import listdir, remove
from os.path import isfile, join, splitext, basename
import subprocess
import re

"""
This script will take in a directory that has videos. For each video it will play it slowly and
allow the user to press various keys (f, b, ...) at the start and end of each stroke. When the
video is over it will output a json file next to the video with the labels.

NOTE: Assumes FFMPEG is installed
"""

FrameNumAndState = namedtuple('FrameNumAndState', ['frame_num', 'state'])


class State(Enum):
    NONE = 0
    TOPSPIN_FOREHAND = 1
    SLICE_FOREHAND = 2
    TOPSPIN_BACKHAND = 3
    SLICE_BACKHAND = 4
    FOREHAND_VOLLEY = 5
    BACKHAND_VOLLEY = 6
    OVERHEAD = 7
    SERVE = 8
    CONTACT = 9


def milli_time():
    return time.time() * 1000


def main(video_dir, video_speed):
    # First find all the videos int he file
    files = [f for f in listdir(video_dir) if isfile(join(video_dir, f))]

    todo_videos = []
    for file in files:
        if file.startswith("."):
            continue

        # TODO: Support more formats
        if not (file.lower().endswith(".mp4") or file.lower().endswith(".mov")):
            print("Skipping {}".format(file))
            continue

        video_name = splitext(basename(file))[0]
        if isfile(join(video_dir, video_name + ".json")):
            print("JSON exists for {}".format(file))
            continue

        todo_videos.append(file)

    for i, file in enumerate(todo_videos):
        print("Doing {} of {} video".format(i, len(todo_videos)))
        if file.startswith("."):
            continue

        # TODO: Support more formats
        if not (file.lower().endswith(".mp4") or file.lower().endswith(".mov")):
            print("Skipping {}".format(file))
            continue

        video_name = splitext(basename(file))[0]
        if isfile(join(video_dir, video_name + ".json")):
            print("JSON exists for {}".format(file))
            continue

        print("Starting to label {}".format(file))
        state_changes = []
        current_state = State.NONE
        state_changes.append(FrameNumAndState(0, current_state))

        video_file_path = join(video_dir, file)
        cap = cv2.VideoCapture(video_file_path)

        cap.set(cv2.CAP_PROP_POS_AVI_RATIO, 1)
        num_of_frames = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        cap.set(cv2.CAP_PROP_POS_AVI_RATIO, 0)
        print("Total num of frames: {}".format(num_of_frames))

        original_fps = get_fps(video_file_path)
        print("FPS: {}".format(original_fps))
        desired_fps = original_fps * video_speed
        usual_wait_amount = round(1000 / desired_fps)
        usual_wait_amount = min(usual_wait_amount, 50)
        last_shown_frame_time = milli_time()

        while cap.isOpened():
            frame_num = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            if frame_num % 1000 == 0:
                print("Frame num: {} of {}".format(frame_num, num_of_frames))
            ret, frame = cap.read()
            if not ret:
                # Break if we are at the end of the video
                break

            wait_amount = max(1, int(usual_wait_amount - (milli_time() - last_shown_frame_time)))

            pressed_key_value = cv2.waitKey(wait_amount)
            normalized_key_value = pressed_key_value & 0xFF
            if normalized_key_value == ord('q'):
                exit(1)
            elif normalized_key_value == ord('f'):
                current_state = state_change_helper(current_state, State.TOPSPIN_FOREHAND, state_changes, frame_num)
            elif normalized_key_value == ord('b'):
                current_state = state_change_helper(current_state, State.TOPSPIN_BACKHAND, state_changes, frame_num)
            elif normalized_key_value == ord('g'):
                current_state = state_change_helper(current_state, State.SLICE_FOREHAND, state_changes, frame_num)
            elif normalized_key_value == ord('n'):
                current_state = state_change_helper(current_state, State.SLICE_BACKHAND, state_changes, frame_num)
            elif normalized_key_value == ord('s'):
                current_state = state_change_helper(current_state, State.SERVE, state_changes, frame_num)
            elif normalized_key_value == ord('c'):
                # Contact is a little odd, because it doesn't change the "current state" even though it gets
                # added to the state changes.
                new_event = FrameNumAndState(frame_num, State.CONTACT)
                print(new_event)
                state_changes.append(new_event)
            elif normalized_key_value == ord('w'):
                print("Current wait amount {}".format(wait_amount))
                print("Press f to go faster, s to go slower")
                key = ""
                while not (key == "s" or key == "f"):
                    pressed_key = cv2.waitKey(0) & 0xFF
                    if pressed_key == ord('s'):
                        key = "s"
                    elif pressed_key == ord('f'):
                        key = "f"
                if key == "s":
                    usual_wait_amount = int(usual_wait_amount * 1.25) + 1
                else:
                    usual_wait_amount = max(1, int(usual_wait_amount * 0.75) - 1)
                print("New wait amount: {}".format(usual_wait_amount))
            elif normalized_key_value == ord('p'):
                cv2.waitKey(0)
            elif normalized_key_value == ord('r'):
                # We want to back up.
                seconds_to_jump_back = 5
                frame_num = int(frame_num - (original_fps * seconds_to_jump_back))
                frame_num = max(0, frame_num)
                # We actually want to jump back to the end of the last stroke that came before
                # this frame_num
                while frame_num < state_changes[-1].frame_num:
                    state_changes = state_changes[:-1]

                while state_changes[-1].state != State.NONE:
                    state_changes = state_changes[:-1]

                frame_num = state_changes[-1].frame_num
                current_state = State.NONE
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num+1)
                print("Rewound to frame {}".format(frame_num))

            cv2.imshow('frame', frame)

            if frame_num == 0:
                print("Ready?")
                cv2.waitKey(0)

            last_shown_frame_time = milli_time()

        cap.release()

        print("Do you want to keep this video? (d) for delete")
        pressed_key_value = cv2.waitKey(0)
        normalized_key_value = pressed_key_value & 0xFF
        if normalized_key_value == ord('d'):
            remove(video_file_path)
            cv2.destroyAllWindows()
            continue

        cv2.destroyAllWindows()

        # Write out all the actions to a json file
        all_actions = []
        for i, change in enumerate(state_changes):
            if i == 0:
                continue
            if change.state == State.NONE:
                new_action = {}
                new_action["video"] = video_file_path
                new_action["label"] = state_changes[i - 2].state.name
                new_action["start"] = state_changes[i - 2].frame_num / original_fps
                new_action["contact"] = state_changes[i - 1].frame_num / original_fps
                new_action["end"] = change.frame_num / original_fps
                new_action["start_frame"] = state_changes[i - 2].frame_num
                new_action["contact_frame"] = state_changes[i - 1].frame_num
                new_action["end_frame"] = change.frame_num
                all_actions.append(new_action)

        with open(join(video_dir, video_name + ".json"), "a") as f:
            f.write(json.dumps(all_actions, indent=2))


def state_change_helper(current_state, new_state, state_changes, current_frame):
    if current_state == new_state:
        current_state = State.NONE
    else:
        current_state = new_state
    new_event = FrameNumAndState(current_frame, current_state)
    print(new_event)
    state_changes.append(new_event)
    return current_state


def check_if_android_fps(video_file_path):
    output = subprocess.run(['ffmpeg', '-i', video_file_path], stderr=subprocess.PIPE).stderr.decode('utf-8')
    search_obj = re.search(r"com.android.capture.fps: (\d+)", output)
    if search_obj:
        return int(search_obj.group(1))
    else:
        return -1


def get_fps(video_file_path):
    output = subprocess.run(['ffmpeg', '-i', video_file_path], stderr=subprocess.PIPE).stderr.decode('utf-8')
    search_obj = re.search(r"(\d+(\.\d+)?) fps", output)
    if search_obj:
        return int(search_obj.group(1))
    else:
        return -1


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Create a label.json file for a video.")
    parser.add_argument("--dir", help="Path to directory where all the training videos are.")
    # parser.add_argument("--tmp_dir", help="Path to the temp dir", default="tmp")
    # parser.add_argument("--fps", type=int, default=240, help="The original fps of the video")
    parser.add_argument("--speed", type=float, default=0.18, help="The speed to try and show the video at")
    args = parser.parse_args()

    main(args.dir, args.speed)
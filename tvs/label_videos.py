import cv2
import argparse
from enum import Enum
import time
from collections import namedtuple
import json
from os import remove
from os.path import isfile, join, splitext, basename
from video_tools import (
    get_movie_files,
    get_total_num_of_frames,
    get_video_fps,
    get_real_world_fps,
)
from file_video_stream import FileVideoStream

"""
This script will take in a directory that has videos. For each video it will play it slowly and
allow the user to press various keys (f, b, ...) at the start and end of each stroke. When the
video is over it will output a json file next to the video with the labels.

NOTE: Assumes FFMPEG is installed
"""

MIN_LOOP_SHOW_MS = 5
FrameNumAndState = namedtuple("FrameNumAndState", ["frame_num", "state"])


class State(Enum):
    """
    Different state that a video can be in.
    """

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
    # First find all the videos in the directory
    videos = get_movie_files(video_dir)

    todo_videos = []
    for file in videos:
        video_name = splitext(basename(str(file)))[0]
        if isfile(join(video_dir, video_name + ".json")):
            # JSON already exists
            continue

        todo_videos.append(str(file))

    for i, file in enumerate(todo_videos):
        print("Doing {} of {} video".format(i + 1, len(todo_videos)))
        print("Starting to label {}".format(file))

        video_name = splitext(basename(file))[0]

        state_changes = []
        current_state = State.NONE
        state_changes.append(FrameNumAndState(0, current_state))

        video_file_path = file

        num_of_frames = get_total_num_of_frames(video_file_path)
        print("Total num of frames: {}".format(num_of_frames))

        # Decide how fast to show the video
        real_world_fps = get_real_world_fps(video_file_path)
        video_fps = get_video_fps(video_file_path)
        if real_world_fps == -1:
            # Have to assume that the real world fps is the same as
            # the video file fps because we don't have another choice
            # Usually this will cause the video to play slower than desired an the user
            # can increase it
            real_world_fps = video_fps
        print("Assumed real_world FPS: {}".format(real_world_fps))
        desired_fps = real_world_fps * video_speed
        desired_time_per_frame = 1000 / desired_fps

        # Set loop variables
        this_loop_desired_time = desired_time_per_frame
        last_shown_frame_time = milli_time()
        loop_start = milli_time()
        fvs = FileVideoStream(video_file_path).start()

        while fvs.more():
            frame_num_and_frame = fvs.read()
            if not frame_num_and_frame:
                # Break if we are at the end of the video
                break
            frame_num, frame = frame_num_and_frame
            if frame_num % 500 == 0:
                print("Frame num: {} of {}".format(frame_num, num_of_frames))

            if not this_loop_desired_time < MIN_LOOP_SHOW_MS:
                cv2.imshow("frame", frame)

            if frame_num == 0:
                print("Ready?")
                cv2.waitKey(0)

            wait_start = milli_time()
            non_wait_time = wait_start - last_shown_frame_time
            wait_amount = max(1, round((this_loop_desired_time - non_wait_time) - 4.5))
            if not this_loop_desired_time < MIN_LOOP_SHOW_MS:
                pressed_key_value = cv2.waitKey(wait_amount)
            else:
                pressed_key_value = -1

            last_shown_frame_time = milli_time()
            loop_time = last_shown_frame_time - loop_start
            this_loop_desired_time = desired_time_per_frame - (
                loop_time - this_loop_desired_time
            )
            loop_start = last_shown_frame_time

            # Rest of stuff
            normalized_key_value = pressed_key_value & 0xFF
            if normalized_key_value == ord("q"):
                exit(1)
            elif normalized_key_value == ord("f"):
                current_state = state_change_helper(
                    current_state, State.TOPSPIN_FOREHAND, state_changes, frame_num
                )
            elif normalized_key_value == ord("b"):
                current_state = state_change_helper(
                    current_state, State.TOPSPIN_BACKHAND, state_changes, frame_num
                )
            elif normalized_key_value == ord("g"):
                current_state = state_change_helper(
                    current_state, State.SLICE_FOREHAND, state_changes, frame_num
                )
            elif normalized_key_value == ord("n"):
                current_state = state_change_helper(
                    current_state, State.SLICE_BACKHAND, state_changes, frame_num
                )
            elif normalized_key_value == ord("s"):
                current_state = state_change_helper(
                    current_state, State.SERVE, state_changes, frame_num
                )
            elif normalized_key_value == ord("c"):
                # Contact is a little odd, because it doesn't change the "current state" even though it gets
                # added to the state changes.
                new_event = FrameNumAndState(frame_num, State.CONTACT)
                print(new_event)
                state_changes.append(new_event)
            elif normalized_key_value == ord("w"):
                print("Current FPS {}".format(desired_fps))
                print("Press f to go faster, s to go slower")
                key = ""
                while not (key == "s" or key == "f"):
                    pressed_key = cv2.waitKey(0) & 0xFF
                    if pressed_key == ord("s"):
                        key = "s"
                    elif pressed_key == ord("f"):
                        key = "f"
                if key == "s":
                    desired_fps -= 10
                else:
                    desired_fps += 10
                desired_time_per_frame = 1000 / desired_fps
                last_shown_frame_time = milli_time()
                loop_start = last_shown_frame_time
                print("New fps: {}".format(desired_fps))
            elif normalized_key_value == ord("p"):
                cv2.waitKey(0)
                last_shown_frame_time = milli_time()
                loop_start = last_shown_frame_time
            elif normalized_key_value == ord("r"):
                # We want to back up.
                seconds_to_jump_back = 5
                frame_num = int(frame_num - (real_world_fps * seconds_to_jump_back))
                frame_num = max(0, frame_num)
                # We actually want to jump back to the end of the last stroke that came before
                # this frame_num
                while frame_num < state_changes[-1].frame_num:
                    state_changes = state_changes[:-1]

                while state_changes[-1].state != State.NONE:
                    state_changes = state_changes[:-1]

                frame_num = state_changes[-1].frame_num
                current_state = State.NONE
                fvs.rewind_to(frame_num)
                print("Rewound to frame {}".format(frame_num))

        print("Do you want to keep this video? (y) for keep, (d) for delete")
        pressed_key_value = cv2.waitKey(0)
        normalized_key_value = pressed_key_value & 0xFF
        if normalized_key_value == ord("d"):
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
                new_action["start"] = state_changes[i - 2].frame_num / video_fps
                new_action["contact"] = state_changes[i - 1].frame_num / video_fps
                new_action["end"] = change.frame_num / video_fps
                new_action["start_frame"] = int(state_changes[i - 2].frame_num)
                new_action["contact_frame"] = int(state_changes[i - 1].frame_num)
                new_action["end_frame"] = int(change.frame_num)
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


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Create json label files for all videos in a folder"
    )
    parser.add_argument(
        "--dir", help="Path to directory where all the training videos are."
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=0.25,
        help="The speed (in real_world_time) to try and show the video at",
    )
    args = parser.parse_args()

    main(args.dir, args.speed)

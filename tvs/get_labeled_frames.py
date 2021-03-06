import cv2
import argparse
import json
import os
import random
import pathlib
from os.path import isfile, join, splitext, basename
from video_tools import get_movie_files, get_total_num_of_frames

"""
Script that takes a directory that has videos that have corresponding json files that list
when strokes happened in them. It will then output a data set of images that has each of the
different phases of a stroke in a different directory.

author akaiser 2021-04-02
"""

# TODO I should parallelize this (maybe? Or maybe wait for a parallelized video parser)

# We are taking videos and creating images, for now we sample this number
# of frames out of each section of each shot. Increasing these will produce
# more files.
NUM_NOTHING_FRAMES = 2
NUM_SET_UP_FRAMES = 2
NUM_CONTACT_FRAMES = 2
NUM_FORWARD_FOLLOW_THROUGH_FRAMES = 2
NUM_BACKWARD_FOLLOW_THROUGH_FRAMES = 2


def main(video_dir, output_dir, validation_percent):
    videos = get_movie_files(video_dir)

    todo_videos = []
    for file in videos:
        if file.startswith("."):
            continue

        video_name = splitext(basename(file))[0]
        if not isfile(join(video_dir, video_name + ".json")):
            print("JSON doesn't exist for {}".format(file))
            exit(1)

        todo_videos.append(file)

    for i, file in enumerate(todo_videos):
        print("Doing {} of {} video".format(i + 1, len(todo_videos)))
        if file.startswith("."):
            continue

        is_training = random.random() > validation_percent
        if is_training:
            folder_type = "train"
        else:
            folder_type = "valid"

        video_file_path = join(video_dir, file)
        vid_name = splitext(basename(video_file_path))[0]

        with open(join(video_dir, vid_name + ".json")) as f:
            all_actions = json.load(f)

        selected_frames = {}
        last_action_frame = 0
        for action in all_actions:
            start_range = action["contact_frame"] - action["start_frame"]
            end_range = action["end_frame"] - action["contact_frame"]
            start_contact_frame = int(action["start_frame"] + int(0.95 * start_range))
            end_contact_frame = int(action["contact_frame"] + int(0.06 * end_range))
            end_forward_motion_frame = int(
                action["contact_frame"] + int(0.245 * end_range)
            )
            for frame in get_sample(
                last_action_frame, int(action["start_frame"]), NUM_NOTHING_FRAMES
            ):
                selected_frames[frame] = "nothing"
            for frame in get_sample(
                int(action["start_frame"]),
                start_contact_frame,
                NUM_SET_UP_FRAMES,
            ):
                selected_frames[frame] = action["label"] + "_set_up"
            for frame in get_sample(
                start_contact_frame,
                end_contact_frame,
                NUM_CONTACT_FRAMES,
            ):
                selected_frames[frame] = action["label"] + "_contact"
            for frame in get_sample(
                end_contact_frame,
                end_forward_motion_frame,
                NUM_FORWARD_FOLLOW_THROUGH_FRAMES,
            ):
                selected_frames[frame] = action["label"] + "_forward_follow_through"
            for frame in get_sample(
                end_forward_motion_frame,
                int(action["end_frame"]),
                NUM_BACKWARD_FOLLOW_THROUGH_FRAMES,
            ):
                selected_frames[frame] = action["label"] + "_backward_follow_through"

        num_of_frames = get_total_num_of_frames(video_file_path)
        print("Total num of frames: {}".format(num_of_frames))

        cap = cv2.VideoCapture(video_file_path)
        while cap.isOpened():
            frame_num = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            if frame_num % 2000 == 0:
                print("Frame num: {} of {}".format(frame_num, num_of_frames))
            ret, frame = cap.read()
            if not ret:
                # Break if we are at the end of the video
                break

            if frame_num in selected_frames:
                shot_type_full_name = selected_frames[frame_num]
                # categories = ["forehand", "backhand", "serve", "nothing"]
                # shot_type = ""
                # for category in categories:
                #     if category in shot_type_full_name.lower():
                #         shot_type = category

                shot_type = shot_type_full_name

                frame_path = os.path.join(
                    output_dir,
                    "data",
                    folder_type,
                    shot_type,
                    "{}-{}.jpg".format(vid_name, int(frame_num)),
                )
                pathlib.Path(frame_path).parent.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(frame_path, frame)


def get_sample(start_frame, end_frame, number_of_frames):
    """
    Take in a start and end frame number and return an iterable with a max size of
    number_of_frames that has a sample of numbers between start and end.
    """
    frame_len = end_frame - start_frame
    if frame_len < number_of_frames:
        return range(start_frame, end_frame)
    else:
        return random.sample(range(start_frame, end_frame), number_of_frames)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create a label.json file for a video."
    )
    parser.add_argument(
        "--dir", help="Path to directory where all the training videos are."
    )
    parser.add_argument(
        "--output_dir",
        default="",
        help="What folder to output the data to, inside this folder a 'data' folder will be created",
    )
    parser.add_argument(
        "--validation_percent",
        type=float,
        default=0.2,
        help="What percent should go in validation set",
    )
    args = parser.parse_args()

    if args.output_dir:
        output_directory = args.output_dir
    else:
        path = pathlib.Path(args.dir)
        output_directory = str(path.parent)

    main(args.dir, output_directory, args.validation_percent)

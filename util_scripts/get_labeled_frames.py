import cv2
import argparse
import json
import os
import random
import pathlib
from os import listdir
from os.path import isfile, join, splitext, basename

# TODO I should parallelize this


def main(video_dir, validation_percent):
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
        if not isfile(join(video_dir, video_name + ".json")):
            print("JSON doesn't exist for {}".format(file))
            exit(1)

        todo_videos.append(file)

    for i, file in enumerate(todo_videos):
        print("Doing {} of {} video".format(i+1, len(todo_videos)))
        if file.startswith("."):
            continue

        is_training = random.random() > validation_percent
        if is_training:
            folder_type = "train"
        else:
            folder_type = "validation"

        video_file_path = join(video_dir, file)
        vid_name = splitext(basename(video_file_path))[0]

        with open(join(video_dir, vid_name + ".json")) as f:
            all_actions = json.load(f)

        selected_frames = {}
        last_action_frame = 0
        for action in all_actions:
            start_range = action["contact_frame"] - action["start_frame"]
            end_range = action["end_frame"] - action["contact_frame"]
            for frame in get_sample(range(last_action_frame, int(action["start_frame"])), 2):
                selected_frames[frame] = "nothing"
            for frame in get_sample(range(int(action["start_frame"]), int(action["start_frame"] + int(0.87 * start_range))), 2):
                selected_frames[frame] = action["label"] + "_set_up"
            for frame in get_sample(range(int(action["start_frame"] + int(0.956 * start_range)), int(action["contact_frame"] + int(0.03 * end_range))), 2):
                selected_frames[frame] = action["label"] + "_contact"
            for frame in get_sample(range(int(action["contact_frame"] + int(0.065 * end_range)), int(action["contact_frame"] + int(0.245 * end_range))), 2):
                selected_frames[frame] = action["label"] + "_forward_follow_through"
            for frame in get_sample(range(int(action["contact_frame"] + int(0.38 * end_range)), int(action["end_frame"])), 2):
                selected_frames[frame] = action["label"] + "_backward_follow_through"
            # TODO -- assuming that the next action doesn't happen within 5 frames
            last_action_frame = int(action["end_frame"] + 5)

        cap = cv2.VideoCapture(video_file_path)

        cap.set(cv2.CAP_PROP_POS_AVI_RATIO, 1)
        num_of_frames = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        cap.set(cv2.CAP_PROP_POS_AVI_RATIO, 0)
        print("Total num of frames: {}".format(num_of_frames))

        while cap.isOpened():
            frame_num = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            if frame_num % 1000 == 0:
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
                    video_dir, "all_pics", folder_type, shot_type, "{}-{}.jpg".format(vid_name, int(frame_num))
                )
                parent_dir = os.path.join(video_dir, "all_pics", folder_type, shot_type)
                pathlib.Path(parent_dir).mkdir(parents=True, exist_ok=True)
                # print("Writing {} to {}".format(frame_num, frame_path))
                cv2.imwrite(frame_path, frame)


def get_sample(possible_range, number_of_frames):
    if len(possible_range) < number_of_frames:
        return possible_range
    else:
        return random.sample(possible_range, number_of_frames)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Create a label.json file for a video.")
    parser.add_argument("--dir", help="Path to directory where all the training videos are.")
    parser.add_argument("--validation_percent", type=float, default=0.2, help="What percent should go in validation set")
    args = parser.parse_args()

    main(args.dir, args.validation_percent)


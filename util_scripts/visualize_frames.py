import numpy as np
import cv2
import argparse
from enum import Enum
import time
from collections import namedtuple
import json
import os


def main(video_file_path, original_fps, video_speed):

    with open(os.path.splitext(os.path.basename(video_file_path))[0] + ".json") as f:
        all_actions = json.load(f)

    before_len = []
    after_len = []
    total_len = []
    for action in all_actions:
        before_len.append(action["contact_frame"] - action["start_frame"])
        after_len.append(action["end_frame"] - action["contact_frame"])
        total_len.append(action["end_frame"] - action["start_frame"])

    total_frames = 18120

    print(len(all_actions))

    print("before: {}".format(sum(before_len) / len(before_len)))
    print("after: {}".format(sum(after_len) / len(after_len)))
    print("total: {}".format(sum(total_len) / len(total_len)))
    # print("Percent: {}".format(interesting_frames / total_frames))

    # print(len(all_actions))
    # cap = cv2.VideoCapture(video_file_path)
    #
    # while cap.isOpened():
    #     frame_num = cap.get(cv2.CAP_PROP_POS_FRAMES)
    #     if frame_num % 1000 == 0:
    #         print("Frame num: {}".format(frame_num))
    #     ret, frame = cap.read()
    #     if not ret:
    #         # Break if we are at the end of the video
    #         break
    #
    #     if frame_num in contact_frames:
    #         cv2.imshow('frame', frame)
    #         pressed_key_value = cv2.waitKey(1000)
    #         normalized_key_value = pressed_key_value & 0xFF
    #         if normalized_key_value == ord('q'):
    #             break


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Create a label.json file for a video."
    )
    parser.add_argument("--video", help="Path to the video file")
    # parser.add_argument("--tmp_dir", help="Path to the temp dir", default="tmp")
    parser.add_argument(
        "--fps", type=int, default=240, help="The original fps of the video"
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=0.18,
        help="The speed to try and show the video at",
    )
    args = parser.parse_args()

    main(args.video, args.fps, args.speed)

import argparse
import os
import sys
import cv2
"""
Command line program that is meant to take in a video file and split it into
many image files in the given output directory.
"""
SECONDS_PER_SCREEN = 0.1


def main(vid, original_fps, out_dir):
    vid_name, _ = os.path.splitext(os.path.basename(vid))
    vid_cap = cv2.VideoCapture(vid)
    success, image = vid_cap.read()
    if original_fps == 0:
        original_fps = vid_cap.get(cv2.CAP_PROP_FPS)
    screen_to_capture = int(SECONDS_PER_SCREEN * original_fps)
    count = 0
    while success:
        if count % screen_to_capture == 0:
            cv2.imwrite(os.path.join(out_dir, vid_name + "frame{}.jpg".format(count)), image)
        success, image = vid_cap.read()
        count += 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split into images")

    parser.add_argument('--fps', type=int, default=0)
    parser.add_argument('vid')
    parser.add_argument('out_dir')

    args = parser.parse_args()

    if not os.path.isdir(args.out_dir):
        print("Output directory is not a directory")
        sys.exit(1)

    if not os.path.isfile(args.vid):
        print("Video file doesn't exist")
        sys.exit(1)

    main(args.vid, args.fps, args.out_dir)
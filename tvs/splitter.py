import argparse
import os

import video_tools
import ai
import helpers

"""
Public methods that can be used by scripts

(1 clip maxes out around 1.45 seconds or 350 frames)
(During interesting get 1/60th seconds)

How the algorithm will work:
Create images for every .1 seconds
Find prob of interesting for those images
Look at 1 second clips every .25 seconds and if > thresh get all images that are interesting
Create images for every 1/60th seconds around those images
Find prob of interesting for those new images
Find clips from those images
Generate final video
"""


def split_video(video_file_path, original_fps, tmp_dir):
    """
    Takes a video and outputs to the output file path a video with
    just the clips of shots
    :param video_file_path:
    :param original_fps:
    :param output_file_path:
    :param tmp_dir:
    :return:
    """
    frames = video_tools.get_video_images(video_file_path, original_fps, 0.1, tmp_dir)
    ai.find_prob_of_interesting(frames)
    interesting_ranges = helpers.find_initial_possibilities(1, .25, 0.7, frames)
    # Maybe put in another loop later, but for now it isn't really needed
    # video_tools.get_more_ranges(frames, interesting_ranges)
    # ai.find_prob_of_interesting(frames)
    # clip_frame_ranges = helpers.find_clip_ranges()
    clip_times = video_tools.convert_frames_to_times(interesting_ranges, frames)
    name = os.path.splitext(os.path.basename(video_file_path))[0]
    video_tools.clip_video(clip_times, video_file_path, tmp_dir + "/" + name + "_imp.mp4")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Split a tennis video into just it's interesting parts.")
    parser.add_argument("--video", help="Path to the video file")
    parser.add_argument("--tmp_dir", help="Path to the temp dir", default="tmp")
    parser.add_argument("--fps", type=int, default=0, help="The original fps of the video")
    args = parser.parse_args()

    split_video(args.video, args.fps, args.tmp_dir)

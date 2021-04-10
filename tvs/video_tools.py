from moviepy.editor import VideoFileClip, concatenate_videoclips
from os import path
import subprocess
import cv2
import re
import mimetypes
from fastai.data.transforms import get_files

"""
Functions related to manipulating video.

NOTE:
Be careful about the fps and time that are used. For each video there is the following:
  "video_time"      : The timestamp in a video, so if you opened the video in quicktime and
                      scanned to a timestamp this is what that is
  "video_fps"       : The set fps of a video.
  "real_world_time" : The actual time that has passed in the real world since the start of the video
  "real_world_fps"  : The number of frames that are in a real_world_time second

If real_world_fps and video_fps are equal then video_time and real_world_time will be equal. However
this isn't always true for slow motion video. For example my pixel will take videos at 240 real world
fps, but save them as 30 "video_fps". This means when you load the clip into quicktime and watch 8 seconds
you'll only have watched 1 real world second. Be very careful which value you are using, also it isn't
always possible to know from metadata what the real_world_fps is, so it may need to be user passed in.
"""


def get_video_fps(video_file_path):
    """
    Get the video_fps of the video at the given path.
    :param video_file_path: The path to the video in question
    :return: The "video_fps" (see comment above) of the video
    """
    if not path.isfile(video_file_path):
        raise Exception(
            "Passed in video_path is not a file: {}".format(video_file_path)
        )

    cap = cv2.VideoCapture(str(video_file_path))
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    cap.release()
    return video_fps


def get_real_world_fps(video_file_path, user_supplied_fps=-1):
    """
    Tries to get the "real_world_fps" of a video, note this isn't very accurate, and
    can fail a lot of the time.
    :param video_file_path:
    :param user_supplied_fps:
    :return: The "real_world_fps" of a video or -1 if it can't find it.
    """
    if user_supplied_fps != -1:
        return user_supplied_fps
    android_fps = get_android_fps_from_ffmpeg(video_file_path)
    if android_fps != -1:
        return android_fps

    return -1


def get_android_fps_from_ffmpeg(video_file_path):
    """
    Tries to look for the com.android.capture.fps metadata tag on a video to get the
    "real_world" fps of a video.
    :param video_file_path: The path to the video file to investigate.
    :return: The com.android.capture.fps if it can find it otherwise -1
    """
    output = subprocess.run(
        ["ffmpeg", "-i", video_file_path], stderr=subprocess.PIPE
    ).stderr.decode("utf-8")
    search_obj = re.search(r"com.android.capture.fps: (\d+(\.\d+)?)", output)
    if search_obj:
        return float(search_obj.group(1))
    else:
        return -1


def get_movie_files(path, recurse=True, folders=None):
    """Get video files in `path` recursively, only in `folders`, if specified."""
    movie_extensions = set(
        k for k, v in mimetypes.types_map.items() if v.startswith("video/")
    )
    return get_files(
        path, extensions=movie_extensions, recurse=recurse, folders=folders
    )


def get_total_num_of_frames(video_file_path):
    cap = cv2.VideoCapture(video_file_path)
    cap.set(cv2.CAP_PROP_POS_AVI_RATIO, 1)
    num_of_frames = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
    cap.release()
    return num_of_frames


def clip_video(times, original_video_path, output_video_path):
    """
    Takes an array that has the start and stop times of video clips and creates
    a video of just those clips at the output path
    TODO: Maybe make this use opencv instead of moviepy
    :param times: List of pair tuples with start and end times (in seconds) of the clips
    :param original_video_path: The path to the original video file
    :param output_video_path: The path to save the output video to
    :return: Doesn't return anything, but outputs the new video to output_video_path
    """
    # What is the fps_source for?
    original_video = VideoFileClip(original_video_path, fps_source="fps")
    clips = []
    for time_pair in times:
        clip = original_video.subclip(time_pair[0], time_pair[1])
        clips.append(clip)
    final_clip = concatenate_videoclips(clips)
    final_clip.write_videofile(output_video_path)


def convert_time_to_frame(time, fps):
    """
    Convert the given time to a specific frame. Be careful of the fps passed in.
    :param time: The time in seconds you want
    :param fps: The fps you are interested in.
    :return:
    """
    return round(time * fps)


def convert_frames_to_times(interesting_ranges, frames):
    clip_times = []
    for frame_range in interesting_ranges:
        start = frames.get_time_of_frame_num(frame_range[0])
        end = frames.get_time_of_frame_num(frame_range[1])
        clip_times.append([start, end])
    return clip_times


def get_frame(vid_cap, frame_num):
    """
    Return the specific frame from the VideoCapture.
    """
    vid_cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
    grabbed, frame = vid_cap.read()
    if grabbed:
        return frame
    else:
        raise Exception("Could not get frame asked for: {}".format(frame_num))


if __name__ == "__main__":
    # Some sort of tests
    test_movie_dir = "data/labled_training_vids"
    for movie in get_movie_files(test_movie_dir):
        video_fps = get_video_fps(movie)
        real_world_fps = get_real_world_fps(movie)
        print(
            "{}\n\tvideo_fps: {}\n\treal_fps: {}".format(
                movie, video_fps, real_world_fps
            )
        )

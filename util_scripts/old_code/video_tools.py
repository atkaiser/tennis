import pathlib
import re

from moviepy.editor import VideoFileClip, concatenate_videoclips
import os
import cv2
import bisect
import helpers

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
    original_video = VideoFileClip(original_video_path, fps_source='fps')
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


class Frame(object):
    """
    DEPRECATED
    """
    def __init__(self, file_path, frame_num):
        self.file_path = file_path
        self.frame_num = frame_num
        frame_dir = os.path.dirname(self.file_path)
        file_name, _ = os.path.splitext(os.path.basename(self.file_path))
        if os.path.isfile(os.path.join(frame_dir, file_name + ".txt")):
            with open(os.path.join(frame_dir, file_name + ".txt"), "r") as f:
                prob = f.read()
                self.prob_interesting = float(prob)
        else:
            self._prob_interesting = None

    @property
    def prob_interesting(self):
        return self._prob_interesting

    @prob_interesting.setter
    def prob_interesting(self, prob_interesting):
        self._prob_interesting = prob_interesting
        frame_dir = os.path.dirname(self.file_path)
        file_name, _ = os.path.splitext(os.path.basename(self.file_path))
        with open(os.path.join(frame_dir, file_name + ".txt"), "w") as f:
            f.write(str(prob_interesting))


class VideoFrames(object):
    def __init__(
        self, file_path, num_of_frames, slowed_down_time_length_in_ms, fps, tmp_dir
    ):
        self.video_file_path = file_path
        self.frames = [None] * num_of_frames
        self.parsed_frames = []
        self.slowed_down_time_length_in_ms = slowed_down_time_length_in_ms
        self.physical_time = num_of_frames / fps
        self.fps = fps
        vid_name, _ = os.path.splitext(os.path.basename(file_path))
        self.name = vid_name
        self.sha1 = helpers.get_sha1_of_file(file_path)
        self.frames_dir = os.path.join(tmp_dir, self.name + "-" + self.sha1)
        pathlib.Path(self.frames_dir).mkdir(parents=True, exist_ok=True)
        for frame in os.listdir(self.frames_dir):
            search_obj = re.search("frame(\d+).jpg", frame)
            if search_obj:
                full_path = os.path.join(self.frames_dir, frame)
                frame_num = int(search_obj.group(1))
                frame = Frame(full_path, frame_num)
                self.set_frame(frame)

    def set_frame(self, frame):
        frame_num = frame.frame_num
        while frame_num >= len(self.frames):
            self.frames.append(None)
            self.physical_time = len(self.frames) / self.fps
        if not self.frames[frame_num]:
            bisect.insort(self.parsed_frames, frame_num)
        self.frames[frame_num] = frame

    def find_frame_closest_to_time(self, time):
        initial_frame = convert_time_to_frame(time, self.fps)
        return helpers.take_closest(self.parsed_frames, initial_frame)

    def get_time_of_frame_num(self, frame_num):
        return (frame_num * (self.slowed_down_time_length_in_ms / len(self.frames))) / 1000

    def find_parsed_frames_between_range(self, start, end):
        """
        Finds all the frames between start and end inclusive that have been parsed
        """
        for i in range(start, end + 1):
            frames_to_return = []
            if self.frames[i]:
                frames_to_return.append(self.frames[i])
            return frames_to_return


def get_video_images(original_video_path, original_fps, seconds_per_screen, tmp_dir):
    """
    DEPRECATED as I no longer want to save images from the video as it takes too long
    I'm keeping this code around for now as a code example of saving images.
    """
    vid_cap = cv2.VideoCapture(original_video_path)
    # Set the capture to the end of the video to get info
    vid_cap.set(cv2.CAP_PROP_POS_AVI_RATIO, 1)
    num_of_frames = int(vid_cap.get(cv2.CAP_PROP_POS_FRAMES))
    total_length_in_ms = int(vid_cap.get(cv2.CAP_PROP_POS_MSEC))
    vid_cap.set(cv2.CAP_PROP_POS_AVI_RATIO, 0)
    if original_fps == 0:
        original_fps = (total_length_in_ms / 1000) / num_of_frames

    frames = VideoFrames(
        original_video_path, num_of_frames, total_length_in_ms, original_fps, tmp_dir
    )

    # import pdb; pdb.set_trace()
    capture_every = round(seconds_per_screen * original_fps)
    frame_num = 0
    success, image = vid_cap.read()
    while success:
        if (
            frame_num % capture_every == 0
            and frame_num < len(frames.frames)
            and not frames.frames[frame_num]
        ):
            frame_path = os.path.join(
                frames.frames_dir, "frame{}.jpg".format(frame_num)
            )
            # frame = Frame(frame_path, frame_num, int(vid_cap.get(cv2.CAP_PROP_POS_MSEC)))
            frame = Frame(frame_path, frame_num)
            cv2.imwrite(frame_path, image)
            frames.set_frame(frame)
        success, image = vid_cap.read()
        frame_num += 1

    return frames


def get_more_ranges(frames, interesting_ranges):
    """
    DEPRECATED, don't use this anymore as I don't want to save images to disk
    This will save as files all the images in the interesting ranges.
    :param frames:
    :param interesting_ranges:
    :return:
    """
    vid_cap = cv2.VideoCapture(frames.video_file_path)
    success, image = vid_cap.read()
    current_range = interesting_ranges.pop(0)
    frame_num = 0
    while success:
        if (
            not frames.frames[frame_num]
            and current_range[0] <= frame_num <= current_range[1]
        ):
            frame_path = os.path.join(
                frames.frames_dir, "frame{}.jpg".format(frame_num)
            )
            frame = Frame(frame_path, frame_num)
            cv2.imwrite(frame_path, image)
            frames.set_frame(frame)
        success, image = vid_cap.read()
        frame_num += 1
        if frame_num > current_range[1]:
            if interesting_ranges:
                current_range = interesting_ranges.pop(0)
            else:
                break


if __name__ == "__main__":
    # Some sort of tests
    # test_video_file_path = "data/test-movs/test.m4v"
    # test_original_fps = 240
    # test_tmp_dir = "tmp"
    # test_frames = get_video_images(
    #     test_video_file_path, test_original_fps, 0.1, test_tmp_dir
    # )

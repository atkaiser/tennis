import bisect
import hashlib


def find_initial_possibilities(window_size, step_size, threshold, video_frames):
    """
    Takes in a video_tools.VideoFrames object and looks over window_size (in seconds)
    intervals to find ones that match a certain threshold per a frame, looks at
    intervals at every step_size. Returns frame ranges that are interesting.
    :param window_size:
    :param step_size:
    :param threshold:
    :param video_frames:
    :return:
    """
    start_of_interval_time = 0

    interesting_ranges = []
    while start_of_interval_time + window_size < video_frames.physical_time:
        start_frame = video_frames.find_frame_closest_to_time(start_of_interval_time)
        end_frame = video_frames.find_frame_closest_to_time(
            start_of_interval_time + window_size
        )
        frames_in_window = video_frames.find_parsed_frames_between_range(
            start_frame, end_frame
        )
        sum_of_frames = sum(frame.prob_interesting for frame in frames_in_window)
        if sum_of_frames / len(frames_in_window) > threshold:
            if interesting_ranges and interesting_ranges[-1][1] >= start_frame:
                last_range = interesting_ranges[-1]
                new_range = (last_range[0], end_frame)
                interesting_ranges.pop()
                interesting_ranges.append(new_range)
            else:
                interesting_ranges.append((start_frame, end_frame))
        start_of_interval_time += step_size
    return interesting_ranges


def get_sha1_of_file(file_path):
    """
    Return the first 10 characters of the sha1 of a file
    :param file:
    :return:
    """
    buf_size = 65536  # lets read stuff in 64kb chunks!
    sha1 = hashlib.sha1()
    with open(file_path, 'rb') as f:
        data = f.read(buf_size)
        while data:
            sha1.update(data)
            data = f.read(buf_size)
    return sha1.hexdigest()[:10]


def take_closest(sorted_list, number):
    pos = bisect.bisect_left(sorted_list, number)
    if pos == 0:
        return sorted_list[0]
    elif pos == len(sorted_list):
        return sorted_list[-1]
    before = sorted_list[pos - 1]
    after = sorted_list[pos]
    if after - number < before - number:
        return after
    else:
        return before

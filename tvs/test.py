import os
import sys
import cv2

vid = "data/test-movs/test.m4v"
out_dir = "tmp"

vid_name, _ = os.path.splitext(os.path.basename(vid))
vid_cap = cv2.VideoCapture(vid)
# success, image = vid_cap.read()
# count = 0
# while success:
#     if count % 10 == 0:
#         cv2.imwrite(os.path.join(out_dir, vid_name + "frame{}.jpg".format(count)), image)
#     success, image = vid_cap.read()
#     count += 1
#     if count % 100 == 0:
#         print(count)


vid_cap.set(cv2.CAP_PROP_POS_AVI_RATIO, 1)
num_of_frames = int(vid_cap.get(cv2.CAP_PROP_POS_FRAMES))
total_length_in_ms = int(vid_cap.get(cv2.CAP_PROP_POS_MSEC))
vid_cap.set(cv2.CAP_PROP_POS_AVI_RATIO, 0)
# if original_fps == 0:
original_fps = (total_length_in_ms / 1000) / num_of_frames

print("Orig fps: {}".format(original_fps))
print("len: {}".format(total_length_in_ms))
print("num frames: {}".format(num_of_frames))
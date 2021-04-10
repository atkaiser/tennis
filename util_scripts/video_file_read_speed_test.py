import cv2
from time import time, sleep
from statistics import mean
from imutils.video import FileVideoStream


def milli_time():
    return time() * 1000


buffer = []
# cap = cv2.VideoCapture("data/labled_training_vids/MVI_4495.MOV")
# cap = cv2.VideoCapture("data/labled_training_vids/IMG_4415.mov")
# cap = cv2.VideoCapture("data/labled_training_vids/IMG_4441.mov")
fvs = FileVideoStream("data/labled_training_vids/MVI_4606.mov").start()
sleep(1)
real_world_fps = 240
video_fps = 30
desired_fps = 30
frames = 0
# while fvs.more():
# while cap.isOpened():
#     ret, frame = cap.read()
#     if not ret:
#         # Break if we are at the end of the video
#         break
#     # frame = fvs.read()
#     buffer.append(frame)
#     if len(buffer) > 480:
#         break

usual_wait_amount = round(1000 / desired_fps)
# usual_wait_amount = min(usual_wait_amount, 50)
last_shown_frame_time = milli_time()

# non_wait_ms = 9.45
# extra_wait_amount = 4.2

loop_times = []
wait_times = []
extra_wait_times = []
non_wait_times = []
start = time()
this_loop_desired_time = usual_wait_amount

loop_start = milli_time()
# for frame in buffer:
# while cap.isOpened():
while fvs.more():
    # ret, frame = cap.read()
    # if not ret:
    #     # Break if we are at the end of the video
    #     break
    frame = fvs.read()
    if frame is None:
        break
    if not this_loop_desired_time < 5:
        cv2.imshow("frame", frame)

    wait_start = milli_time()
    non_wait_time = wait_start - last_shown_frame_time
    non_wait_times.append(non_wait_time)
    wait_amount = max(1, round((this_loop_desired_time - non_wait_time) - 4.5))
    if not this_loop_desired_time < 5:
        pressed_key_value = cv2.waitKey(wait_amount)
    last_shown_frame_time = milli_time()
    loop_time = last_shown_frame_time - loop_start
    print("last loop desired time : {}".format(this_loop_desired_time))
    print("last loop time         : {}".format(loop_time))
    this_loop_desired_time = usual_wait_amount - (loop_time - this_loop_desired_time)
    print("this loop desired time : {}".format(this_loop_desired_time))
    print("")
    loop_times.append(loop_time)
    wait_time = last_shown_frame_time - wait_start
    wait_times.append(wait_time)
    extra_wait_times.append(wait_time - wait_amount)
    loop_start = last_shown_frame_time
    frames += 1

elapsed = time() - start
print("")
print("avg loop time: {}".format(sum(loop_times[1:]) / len(loop_times[1:])))
print("avg wait: {}".format(sum(wait_times) / len(wait_times)))
print("avg non_wait_ms: {}".format(sum(non_wait_times[1:]) / len(non_wait_times[1:])))
print("avg extra wait: {}".format(sum(extra_wait_times) / len(extra_wait_times)))
print("desired_avg loop time: {}".format(usual_wait_amount))
print("elapsed: {}".format(elapsed))
print("frames: {}".format(frames))
print("FPS: {}".format(frames / elapsed))
print("desired fps: {}".format(desired_fps))


#
# time.sleep(1.0)
#
# while fvs.more():
#     frame = fvs.read()
#     # cv2.imshow("Frame", frame)

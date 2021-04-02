import cv2
from imutils.video import FileVideoStream
from time import time, sleep
from statistics import mean


# cap = cv2.VideoCapture("../training_videos/20210325_backhands.mp4")
cap = cv2.VideoCapture("../data/to_process/VID_20200218_131507.mp4")
# fvs = FileVideoStream("../training_videos/20210325_backhands.mp4").start()
sleep(1.0)
cap_times = []
while cap.isOpened():
# while fvs.more():
    loop_start = time()
    # frame_num = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
    # if frame_num % 1000 == 0:
    #     print("Frame num: {} of {}".format(frame_num, num_of_frames))
    ret, frame = cap.read()
    # frame = fvs.read()
    if not ret:
        # Break if we are at the end of the video
        break
    elapsed = time() - loop_start
    cap_times.append(elapsed)
average = mean(cap_times)
fps = 1/average
print(f'Avg cap time: {average}')
print(f'FPS: {fps}')




#
# time.sleep(1.0)
#
# while fvs.more():
#     frame = fvs.read()
#     # cv2.imshow("Frame", frame)


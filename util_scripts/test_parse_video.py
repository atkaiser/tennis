from fastbook import *
from fastai.vision.widgets import *
import cv2
from time import time
import argparse

def moving_average(numbers, window_size):
    if window_size % 2 == 0:
        window_size -= 1
    each_side = int((window_size - 1) / 2)
    moving_averages = []
    i = 0
    while i < len(numbers):
        start = max(0, i - each_side)
        end = min(len(numbers) - 1, i + each_side) + 1
        this_window = numbers[start:end]
        window_average = sum(this_window) / len(this_window)
        moving_averages.append(window_average)
        i += 1
    return moving_averages


parser = argparse.ArgumentParser(description="TODO")
parser.add_argument("--video_path", help="Path to directory where all the training videos are.",
                    default="../data/to_process/VID_20200218_131507.mp4")
parser.add_argument("--fps", type=int, default=-1,
                    help="The original fps of the video, if not supplied this will try to be guessed using ffmpeg")
parser.add_argument("--model", default="../models/new_forehand_backhand/export.pkl", help="Path to the file containing the model")

args = parser.parse_args()

learn_inf = load_learner(args.model)
vocab = learn_inf.dls.vocab

start_time = time()
cap = cv2.VideoCapture(args.video_path)

fps = args.fps
predict_every = 8

cap.set(cv2.CAP_PROP_POS_AVI_RATIO, 1)
num_of_frames = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
cap.set(cv2.CAP_PROP_POS_AVI_RATIO, 0)
print("Total num of frames: {}".format(num_of_frames))

batch_labels = []
batch = []
x = []
results = []
batch_size = 64

while cap.isOpened():
    frame_num = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
    if frame_num % 500 == 0:
        print("Frame num: {} of {}".format(frame_num, num_of_frames))
    ret, frame = cap.read()
    if not ret:
        # Break if we are at the end of the video
        break
    if frame_num % predict_every != 0:
        continue
    x.append(frame_num / fps)
    batch.append(frame)
    if len(batch) >= batch_size:
        dl = learn_inf.dls.test_dl(batch, num_workers=0)
        inp, preds, _, dec_preds = learn_inf.get_preds(dl=dl, with_input=True, with_decoded=True)
        for pred in preds:
            results.append(pred)
        batch = []

if len(batch) > 0:
    dl = learn_inf.dls.test_dl(batch, num_workers=0)
    inp, preds, _, dec_preds = learn_inf.get_preds(dl=dl, with_input=True, with_decoded=True)
    for pred in preds:
        results.append(pred)

end_time = time()
print("Total seconds: {}".format(end_time - start_time))

vid = [str(int(sec / 60)) + ":" + str(int(sec % 60)) for sec in x]

nothing_index = list(learn_inf.dls.vocab).index("nothing")

# At the end we want a frame number for contact and type of shot for each frame
# Simple algorithm:
# 1. Find all possible shots into a list
# 2. Go through that list and combine all shots that could be for the same thing
possible_shots = []
for i, row in enumerate(results):
    if row[nothing_index] < 0.5:
        possible_shots.append((row[nothing_index].item(), x[i], vocab[row.argmax(dim=-1).item()]))

# print(possible_shots)

from scipy import signal
prob_something = [1 - frame[0] for frame in possible_shots]
peaks, _ = signal.find_peaks(prob_something, distance=int(480/predict_every))
print(peaks)

import matplotlib.pyplot as plt

plt.plot([possible_shots[peak][1] for peak in peaks], [prob_something[peak] for peak in peaks], "xr")
plt.plot([frame[1] for frame in possible_shots], prob_something)
plt.show()


# start_of_current_shot = possible_shots[0]
# for frame in possible_shots[1:]:
#     if frame
#     print(frame)

# Graph
# window = 120
# actual_window = int(window / predict_every)
# print(actual_window)
# fig = go.Figure()
# for i, cat in enumerate(vocab):
#     fig.add_trace(go.Scatter(x=vid, y=moving_average([row[i].item() for row in results], actual_window),
#                         mode='lines+markers',
#                         name=cat))
# fig.show()
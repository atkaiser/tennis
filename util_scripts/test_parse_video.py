from fastbook import *
from fastai.vision.widgets import *
import cv2
# import plotly.graph_objects as go
from time import time

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


learn_inf = load_learner('../models/new_forehand_backhand/export.pkl').to_fp16()
vocab = learn_inf.dls.vocab
learn_inf.no_bar()
learn_inf.no_logging()
learn_inf.no_mbar()

start_time = time()
# cap = cv2.VideoCapture("/storage/my_data/vids/short.mp4")
# cap = cv2.VideoCapture("/storage/my_data/vids/rally_test.mp4")
cap = cv2.VideoCapture("../data/to_process/VID_20200218_131507.mp4")

fps = 30
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
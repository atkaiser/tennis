import argparse
import os
import sys
import cv2
import pickle
from fastai.imports import *

from fastai.transforms import *
from fastai.conv_learner import *
from fastai.model import *
from fastai.dataset import *
from fastai.sgdr import *
from fastai.plots import *
from moviepy.editor import VideoFileClip, concatenate_videoclips
"""
TODO
"""
SECONDS_PER_SCREEN = 0.1


def main(vid, original_fps, out_dir, tmp_dir):
    vid_name, _ = os.path.splitext(os.path.basename(vid))
    vid_cap = cv2.VideoCapture(vid)
    success, image = vid_cap.read()
    count = 0
    while success:
        cv2.imwrite(os.path.join(tmp_dir, vid_name + "frame{}.jpg".format(count)), image)
        success, image = vid_cap.read()
        count += 1

    print("Number of frames: {}".format(count))
    # count = 3994

    # Load the model
    PATH = "/Users/akaiser/random/data/tennis/"
    sz = 256
    arch = resnet34
    data = ImageClassifierData.from_paths(PATH, tfms=tfms_from_model(arch, sz))
    learn = ConvLearner.pretrained(arch, data, precompute=True)
    learn.load('first_int_vs_non_tennis_classifier')
    learn.precompute = False
    _, val_tfms = tfms_from_model(arch, sz)

    probabilities = []
    for n in tqdm(range(count)):
        file_name = os.path.join(tmp_dir, vid_name + "frame{}.jpg".format(n))
        im_orig = open_image(file_name)
        im = val_tfms(im_orig)
        predictions = learn.predict_array(im[None])
        prob_of_interesting = np.exp(predictions[:, 0])
        probabilities.append(prob_of_interesting[0])

    # pickle.dump(probabilities, open("/tmp/prob.p", "wb"))
    # probabilities = pickle.load(open("/tmp/prob.p", "rb"))

    width = 400
    step = 10
    start = 0
    tipping_point = 300
    good = {}
    last_good = -1
    while start + width < count:
        end = start + width
        s = sum(probabilities[start:end])
        if s > tipping_point:
            if last_good > 0:
                if s > good[last_good]:
                    del good[last_good]
                    last_good = start
                    good[start] = s
            else:
                last_good = start
                good[start] = s
        else:
            last_good = -1
        start += step

    original_fps = vid_cap.get(cv2.CAP_PROP_FPS)
    clips = []
    for key in good:
        start_time = key / original_fps
        end_time = (key + width) / original_fps
        print("{} {}".format(start_time, end_time))
        clip = VideoFileClip(vid).subclip(start_time, end_time)
        clips.append(clip)
    final_clip = concatenate_videoclips(clips)
    final_clip.write_videofile("final.mp4")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clip")

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

    main(args.vid, args.fps, args.out_dir, args.out_dir)
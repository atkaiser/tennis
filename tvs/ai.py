from fastai.vision import *
from tqdm import tqdm


def find_prob_of_interesting(frames):
    """
    Find the probability that a frame is interesting using a pretrained
    neural network.
    :param frames: Is a video_tools.VideoFrames object
    :return: None, updates the values in the frames object
    """
    # Load the model
    path = Path('models/tennis_int')
    learn = load_learner(path)

    unlabeled_frames = [
        frame
        for frame in frames.frames
        if frame is not None and not frame.prob_interesting
    ]
    if unlabeled_frames:
        for frame in tqdm(unlabeled_frames):
            file_name = frame.file_path
            img = open_image(file_name)
            pred_class, pred_idx, outputs = learn.predict(img)
            prob_of_interesting = outputs.numpy()[0]
            frame.prob_interesting = prob_of_interesting

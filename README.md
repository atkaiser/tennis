## General overview

The purpose of this project is to take in a video clip of someone playing tennis and return a video that just has the clips of them hitting the ball. A strech goal would also be able to control the speed of the output video.

## Steps needed

To achieve the goal above I will be trying to use machine learning, so to get to a final product there are some steps along the way.  This is a discussion of each step and possible options/complications

1. Label test videos
    1. To be able to use machine learning you need a test set.
    2. First step is to find videos, I found 3 sets of videos
        1. Videos of me taken mostly from the side
        2. Videos of pros taken when I went to Indian Wells in 2019
        3. Random videos off of Instagram (pretty easy to find lots of clips and can get a good variety
    3. Next you need a way to manually label when there are certain shots in the videos, I did this by writing `util_scripts/label_video.py`. The output of this is a json file that goes next to the video that labels start, contact point, and stop of each shot and what type of shot it is.
    4. Note: It's important to get this correct, otherwise you have to fix things later when training the model which can take a bunch of time.
2. Create training/validation sets
    1. The output from the label step just has a json of the video, but fastai expects images in a certain format.  The `util_scripts/get_labeled_frames.py` takes a folder with videos and jsons from step 1 and extracts images and puts them in a format that can be passed into fastai.
3. Generate the model
    1. From the output of step 2 you need to run fastai (on a GPU somewhere) to train the model
    2. There are a couple of options here for what exactly you are training for
        1. The simplest is to train in categories forehand, backhand, nothing
        2. You could also train in stricter categories like start_forehand, contact_forehand, end_forehand, ...
    3. As with anything from fastai, there are a lot of options for training, i.e.
        1. Augmentations
        2. Learning rate
        3. Training iterations.
    4. Also ususally the test set isn't labeled 100% correctly, so fixing that can take a lot of time.
4. Turning the model into something useful
    1. The model you get from fastai takes in an image and returns proabilities of what it thinks it is, but what you need is when a shot occured.
    2. It's hard to run the model on every frame, because that would be really, really slow
    3. Here are some options:
        1. Take the model and run every few frames, then try and look at the sequence and develop some rules for when a shot happened. So far I found this to not be too reliable, in that some shots "activate" the model a lot more than others, so it's hard to find a good balance, current idea:
            1. Run the model every X frames
            2. Run the moving average on that data
            3. Use scipy.signal.find_peaks to find the bottoms of the data with some threshold
            4. Each bottom is a shot, then find the highest contact moment and declare that contact point
        2. Train a second model to take in a sequence of activations (haven't tried this, but it sounds interesting)
5. Clip the original video

One thing that is hard to balance that I've noticed, is that each step effects what you do in each of the other steps. The biggest example is that if you come up with a good enough model in step 3, then step 4 will be pretty easy. But if the model is noisy then you have to do a lot more work in step 4 to remove the noise. But it continues backwards, in that your model will only be good if you have good data to train on, so you can try cleaning up your data well in step 3 or you can try and do better in step 1 and 2 so that you only output "clean" data.

## Environment setup

The virtual env for this is tennis and was set up like:

(Not sure if this first part is needed or not??)
```bash
brew install tcl-tk
export CPPFLAGS="-I/usr/local/opt/tcl-tk/include"
export LDFLAGS="-L/usr/local/opt/tcl-tk/lib"
```

```bash
pyenv install 3.9.2
mkvirtualenv fastai -p ~/.pyenv/versions/3.9.2/bin/python
pip install -r requirements.txt
```

To use run (TODO fix this):

`python tvs/splitter.py --video <path-to-video> --fps 240`
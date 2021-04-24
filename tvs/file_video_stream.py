from threading import Thread
import cv2
import time
from queue import Queue

"""
This is a modified version of imutils.FileVideoStream that allows you to
get the frame number of a frame as well as be able to seek back and forth
in a video.
"""


class FileVideoStream:
    def __init__(self, path, transform=None, queue_size=128):
        # initialize the file video stream along with the boolean
        # used to indicate if the thread should be stopped or not
        self.stream = cv2.VideoCapture(path)
        self.stopped = False
        self.transform = transform

        # initialize the queue used to store frames read from
        # the video file
        self.Q = Queue(maxsize=queue_size)
        # intialize thread
        self.thread = Thread(target=self.update, args=())
        self.thread.daemon = True
        self.rewind_frame_num = -1

    def start(self):
        # start a thread to read frames from the file video stream
        self.thread.start()
        return self

    def update(self):
        # keep looping infinitely
        while True:
            # if the thread indicator variable is set, stop the
            # thread
            if self.stopped:
                break

            if self.rewind_frame_num != -1:
                print("Found rewind of frame to {}".format(self.rewind_frame_num))
                self.Q = Queue(maxsize=self.Q.maxsize)
                self.stream.set(cv2.CAP_PROP_POS_FRAMES, self.rewind_frame_num)
                self.rewind_frame_num = -1

            # otherwise, ensure the queue has room in it
            if not self.Q.full():
                frame_num = int(self.stream.get(cv2.CAP_PROP_POS_FRAMES))
                # read the next frame from the file
                (grabbed, frame) = self.stream.read()

                # if the `grabbed` boolean is `False`, then we have
                # reached the end of the video file
                if not grabbed:
                    self.stopped = True
                    continue

                if self.transform:
                    frame = self.transform(frame)

                # add the frame to the queue
                self.Q.put((frame_num, frame))
            else:
                time.sleep(0.1)  # Rest for 10ms, we have a full queue

        self.stream.release()

    def read(self):
        # return next frame in the queue
        return self.Q.get()

    # Insufficient to have consumer use while(more()) which does
    # not take into account if the producer has reached end of
    # file stream.
    def running(self):
        return self.more() or not self.stopped

    def more(self):
        # return True if there are still frames in the queue. If stream is not stopped, try to wait a moment
        tries = 0
        while self.Q.qsize() == 0 and not self.stopped and tries < 5:
            time.sleep(0.1)
            tries += 1

        return self.Q.qsize() > 0

    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True
        # wait until stream resources are released (producer thread might be still grabbing frame)
        self.thread.join()

    def rewind_to(self, frame_num):
        self.rewind_frame_num = frame_num
        print("Set rewind to {}".format(frame_num))
        if self.stopped:
            self.stopped = False
            self.thread = Thread(target=self.update, args=())
            self.thread.daemon = True

        while self.rewind_frame_num != -1:
            time.sleep(0.05)

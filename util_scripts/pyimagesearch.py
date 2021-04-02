# import the necessary packages
from __future__ import print_function
from imutils.object_detection import non_max_suppression
from imutils import paths
import numpy as np
import argparse
import imutils
import cv2
# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video", required=True, help="path to video")
args = vars(ap.parse_args())
# initialize the HOG descriptor/person detector
hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

cap = cv2.VideoCapture(args["video"])

# loop over the image paths
while cap.isOpened():
    frame_num = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
    if frame_num % 1000 == 0:
        print("Frame num: {} of {}".format(frame_num, 0))
    ret, frame = cap.read()
    if not ret:
        # Break if we are at the end of the video
        break
    # load the image and resize it to (1) reduce detection time
    # and (2) improve detection accuracy
    # image = cv2.imread(imagePath)
    image = frame
    image = imutils.resize(image, width=min(400, image.shape[1]))
    orig = image.copy()
    # detect people in the image
    (rects, weights) = hog.detectMultiScale(image, winStride=(4, 4), padding=(8, 8), scale=1.1)
    # draw the original bounding boxes
    # for (x, y, w, h) in rects:
    #     cv2.rectangle(orig, (x, y), (x + w, y + h), (0, 0, 255), 2)
    # apply non-maxima suppression to the bounding boxes using a
    # fairly large overlap threshold to try to maintain overlapping
    # boxes that are still people
    rects = np.array([[x, y, x + w, y + h] for (x, y, w, h) in rects])
    picks = non_max_suppression(rects, probs=None, overlapThresh=0.65)
    # draw the final bounding boxes
    for (xA, yA, xB, yB) in picks:
        width = xB - xA
        height = yB - yA
        middle = (int((xA + xB)/2), int((yA + yB)/2))
        radius = int(max(width, height) / 2)
        cv2.rectangle(image, (middle[0] - radius, middle[1] - radius), (middle[0] + radius, middle[1] + radius),
                      (0, 0, 255), 2)
        cv2.rectangle(image, (xA, yA), (xB, yB), (0, 255, 0), 2)
    # show some information on the number of bounding boxes
    # filename = imagePath[imagePath.rfind("/") + 1:]
    # print("[INFO] {}: {} original boxes, {} after suppression".format(
    #     "mov", len(rects), len(picks)))
    # show the output images
    # cv2.imshow("Before NMS", orig)
    cv2.imshow("After NMS", image)
    pressed_key_value = cv2.waitKey(1)
    normalized_key_value = pressed_key_value & 0xFF
    if normalized_key_value == ord('q'):
        break
    elif normalized_key_value == ord('p'):
        cv2.waitKey(0)


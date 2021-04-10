# Works, but you get a 30 fps movie at the end, which isn't great
# from moviepy.editor import *
#
# # loading video gfg
# clip = VideoFileClip("tmp/short.mp4")
#
# # applying speed effect
# final_clip = clip.fx(vfx.speedx, 4)
#
# final_clip.write_videofile("fast.mp4")


import cv2

# Create an object to read
# from camera
# video = cv2.VideoCapture(0)
video = cv2.VideoCapture("tmp/PXL_20210325_182546619.mp4")

# We need to set resolutions.
# so, convert them from float to integer.
frame_width = int(video.get(3))
frame_height = int(video.get(4))

size = (frame_width, frame_height)

# Below VideoWriter object will create
# a frame of above defined The output
# is stored in 'filename.avi' file.
result = cv2.VideoWriter(
    "create_ml_training_data/mix.mp4", cv2.VideoWriter_fourcc(*"X264"), 120, size
)

frame_num = 0
while True:
    ret, frame = video.read()

    if not ret:
        break

    if frame_num % 2 == 0:
        result.write(frame)
    frame_num += 1

# When everything done, release
# the video capture and video
# write objects
video.release()
result.release()

# Closes all the frames
cv2.destroyAllWindows()

print("The video was successfully saved")

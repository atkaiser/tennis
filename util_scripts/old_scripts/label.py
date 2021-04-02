import argparse
import os
import sys
import re
import cv2

"""
First try at labeling images. This works by taking in a directory of images
and then sorting those images into separate labeled directories.

NOTE: Deprecated, this was my first attempt to label things, it works on photos
Please don't continue using this. 
"""

labels = {}
labels["c"] = "nothing"
labels["d"] = "start-forehand"
labels["f"] = "forehand"
labels["g"] = "end-forehand"
labels["v"] = "start-backhand"
labels["b"] = "backhand"
labels["n"] = "end-backhand"

possible_keys = {}
possible_keys[ord("s")] = "s"
possible_keys[ord("u")] = "u"
for key in labels:
    possible_keys[ord(key)] = key


def get_file_sortable(file_name):
    sortable = file_name.split("frame")
    sortable[1] = int(sortable[1].split(".")[0])
    return sortable


def main(photos_dir, out_dir):
    files = []
    for filename in os.listdir(photos_dir):
        if not filename.startswith("."):
            files.append(os.path.join(photos_dir, filename))
    files = sorted(files, key=get_file_sortable)
    for label in labels:
        print("{} : {}".format(label, labels[label]))
    for image_file in files:
        image = cv2.imread(image_file)
        cv2.imshow(image_file, image)
        k = cv2.waitKey(0)
        while k not in possible_keys:
            k = cv2.waitKey(0)
        if k == ord("s"):
            break
        elif k == ord("u"):
            pass
            # TODO undo the last label
        else:
            input_char = possible_keys[k]
            label_folder = labels[input_char]
            moved_dir = os.path.join(out_dir, label_folder)
            if not os.path.exists(moved_dir):
                os.makedirs(moved_dir)
            output_path = os.path.join(moved_dir, os.path.basename(image_file))
            os.rename(image_file, output_path)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Label images")

    parser.add_argument("photos_dir")
    parser.add_argument("out_dir")

    args = parser.parse_args()

    if not os.path.isdir(args.out_dir):
        print("Output directory is not a directory")
        sys.exit(1)

    if not os.path.isdir(args.photos_dir):
        print("Input directory is not a directory")
        sys.exit(1)

    main(args.photos_dir, args.out_dir)

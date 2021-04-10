# from fastai.imports import *
#
# from fastai.transforms import *
# from fastai.conv_learner import *
# from fastai.model import *
# from fastai.dataset import *
# from fastai.sgdr import *
# from fastai.plots import *
#
# PATH = "/Users/akaiser/random/data/tennis/"
#
# sz = 256
# arch = resnet34
# data = ImageClassifierData.from_paths(PATH, tfms=tfms_from_model(arch, sz))
# learn = ConvLearner.pretrained(arch, data, precompute=True)
#
# # learn.fit(0.07, 2)
# learn.load('first_int_vs_non_tennis_classifier')
#
# total = 0
# correct = 0
# learn.precompute=False
# _, val_tfms = tfms_from_model(arch,sz)
# folder = "/Users/akaiser/Documents/workspace/tennis/data/sorted/side-angle/nothing"
# for f in tqdm(os.listdir(folder)[2000:3000]):
#     total += 1
#     im_orig = open_image(folder + "/" + f)
#     im = val_tfms(im_orig)
#     predictions = learn.predict_array(im[None])
#     if np.argmax(predictions) == 1:
#         correct += 1
# print("{} / {}".format(correct, total))

from fastai.vision import *

defaults.device = torch.device("cpu")
path = Path("models/tennis_int")
learn = load_learner(path)

img = open_image(
    "/Users/akaiser/Documents/workspace/tennis/data/sorted/side-angle/nothing/IMG_4230frame10116.jpg"
)
pred_class, pred_idx, outputs = learn.predict(img)
print(pred_class)

import torch

from imageio import imread, imsave
from skimage.transform import resize as imresize
import numpy as np
from path import Path
import argparse
#from tqdm import tqdm

from inverse_warp import pose_vec2mat
from scipy.ndimage.interpolation import zoom

from inverse_warp import *

import models
from utils import tensor2array

import vo_single_pkg 

#import cv2

parser = argparse.ArgumentParser(description='Script for visualizing depth map and masks',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--pretrained-posenet", required=True, type=str, help="pretrained PoseNet path")
parser.add_argument("--img-height", default=256, type=int, help="Image height")
parser.add_argument("--img-width", default=832, type=int, help="Image width")
parser.add_argument("--no-resize", action='store_true', help="no resizing is done")

parser.add_argument("--tensor-img-1", type=str, help="Tensor image 1")
parser.add_argument("--tensor-img-2", type=str, help="Tensor image 2")
parser.add_argument("--output-dir", type=str, help="Output directory for saving predictions in a big 3D numpy file")
parser.add_argument("--img-exts", default=['png', 'jpg', 'bmp'], nargs='*', type=str, help="images extensions to glob")
parser.add_argument("--rotation-mode", default='euler', choices=['euler', 'quat'], type=str)

parser.add_argument("--sequence", default='09', type=str, help="sequence to test")
device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")


def load_tensor_image(filename, args):
    img = imread(filename).astype(np.float32)
    h, w, _ = img.shape
    if (not args.no_resize) and (h != args.img_height or w != args.img_width):
        img = imresize(img, (args.img_height, args.img_width)).astype(np.float32)
    img = np.transpose(img, (2, 0, 1))
    tensor_img = ((torch.from_numpy(img).unsqueeze(0)/255-0.45)/0.225).to(device)
    return tensor_img


@torch.no_grad()
def main():
    args = parser.parse_args()

    weights_pose = torch.load(args.pretrained_posenet)
    pose_net = models.PoseResNet().to(device)
    pose_net.load_state_dict(weights_pose['state_dict'], strict=False)
    pose_net.eval()

    output_dir = Path(args.output_dir)
    output_dir.makedirs_p()

    test_files = [args.tensor_img_1, args.tensor_img_2]

    print('{} files to test'.format(len(test_files)))
    print(device)
    #print(test_files)

    global_pose = np.eye(4)
    poses = [global_pose[0:3, :].reshape(1, 12)]

    n = len(test_files)

    vo_single_pkg.estimate_pose(pose_net, test_files, args, device)

    #poses = np.concatenate(poses, axis=0)
    #filename = Path(args.output_dir + args.sequence + ".txt")
    #np.savetxt(filename, poses, delimiter=' ', fmt='%1.8e')


if __name__ == '__main__':
    main()

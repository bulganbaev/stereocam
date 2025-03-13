# -*-coding: utf-8 -*-
"""
    @Author : bulganbaev
    @E-mail : bulganbaev@gmail.com
    @Date   : 2020-04-10 18:24:06
"""

import os
import cv2
import argparse
import numpy as np
from core.utils import image_utils, file_utils
from core import camera_params, stereo_matcher
from core.camera_driver import CameraDriver  # Импортируем CameraDriver


class StereoDepth(object):
    """Класс для работы с двумя камерами и получения 3D-точек."""

    def __init__(self, stereo_file, width=1920, height=1080, filter=True, use_open3d=True, use_pcl=False):
        self.count = 0
        self.filter = filter
        self.camera_config = camera_params.get_stereo_coefficients(stereo_file)
        self.use_pcl = use_pcl
        self.use_open3d = use_open3d

        assert (width, height) == self.camera_config["size"], f"Error: expected size {self.camera_config['size']}"

    def capture2(self, left_camera_id, right_camera_id):
        """Захват видео с двух камер с использованием CameraDriver."""
        camL = CameraDriver(camera_id=left_camera_id, width=1920, height=1080, flip_horizontal=True, flip_vertical=True)
        camR = CameraDriver(camera_id=right_camera_id, width=1920, height=1080, flip_vertical=True, flip_horizontal=True)

        camL.start_camera()
        camR.start_camera()
        self.count = 0

        while True:
            frameL = camL.get_frame()
            frameR = camR.get_frame()

            if frameL is None or frameR is None:
                print("Ожидание кадров...")
                continue

            self.task(frameL, frameR, waitKey=50)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        camL.stop_camera()
        camR.stop_camera()
        cv2.destroyAllWindows()

    def get_rectify_image(self, imgL, imgR):
        left_map_x, left_map_y = self.camera_config["left_map_x"], self.camera_config["left_map_y"]
        right_map_x, right_map_y = self.camera_config["right_map_x"], self.camera_config["right_map_y"]
        rectifiedL = cv2.remap(imgL, left_map_x, left_map_y, cv2.INTER_LINEAR)
        rectifiedR = cv2.remap(imgR, right_map_x, right_map_y, cv2.INTER_LINEAR)
        return rectifiedL, rectifiedR

    def task(self, frameL, frameR, waitKey=5):
        rectifiedL, rectifiedR = self.get_rectify_image(frameL, frameR)
        grayL = cv2.cvtColor(rectifiedL, cv2.COLOR_BGR2GRAY)
        grayR = cv2.cvtColor(rectifiedR, cv2.COLOR_BGR2GRAY)
        dispL = self.get_disparity(grayL, grayR, self.filter)
        points_3d = self.get_3dpoints(dispL, Q=self.camera_config["Q"])
        self.show_2dimage(frameL, frameR, points_3d, dispL, waitKey=waitKey)

    def get_disparity(self, imgL, imgR, use_wls=True):
        return stereo_matcher.get_filter_disparity(imgL, imgR, use_wls=use_wls)

    def get_3dpoints(self, disparity, Q, scale=1.0):
        points_3d = cv2.reprojectImageTo3D(disparity, Q) * scale
        return np.asarray(points_3d, dtype=np.float32)

    def show_2dimage(self, frameL, frameR, points_3d, dispL, waitKey=0):
        depth_colormap = stereo_matcher.get_visual_depth(points_3d[:, :, 2])
        dispL_colormap = stereo_matcher.get_visual_disparity(dispL)
        cv2.imshow('left', frameL)
        cv2.imshow('right', frameR)
        cv2.imshow('disparity-color', dispL_colormap)
        cv2.imshow('depth-color', depth_colormap)
        cv2.waitKey(waitKey)


def get_parser():
    parser = argparse.ArgumentParser(description='Stereo Camera Calibration')
    parser.add_argument('--stereo_file', type=str, default='configs/camera/stereo_cam.yml', help='Stereo calibration file')
    parser.add_argument('--left_camera', type=int, default=0, help='Left camera ID')
    parser.add_argument('--right_camera', type=int, default=1, help='Right camera ID')
    parser.add_argument('--filter', type=bool, default=True, help='Use WLS filter')
    return parser


if __name__ == '__main__':
    args = get_parser().parse_args()
    stereo = StereoDepth(args.stereo_file, filter=args.filter, use_open3d=True)
    stereo.capture2(left_camera_id=args.left_camera, right_camera_id=args.right_camera)
    cv2.destroyAllWindows()

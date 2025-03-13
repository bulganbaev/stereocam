import os
import argparse
import cv2
import time
from core.camera_driver import CameraDriver  # Импорт твоего драйвера

class StereoCamera:
    """Класс для работы с двумя камерами, использует CameraDriver вместо cv2.VideoCapture."""

    def __init__(self, chess_width, chess_height, detect=False):
        """
        :param chess_width: Количество пересечений шахматной доски по ширине.
        :param chess_height: Количество пересечений шахматной доски по высоте.
        :param detect: Включить ли автоматическое обнаружение шахматной доски.
        """
        self.chess_width = chess_width
        self.chess_height = chess_height
        self.detect = detect
        self.criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    def detect_chessboard(self, image):
        """Обнаружение шахматной доски в кадре."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        ret, corners = cv2.findChessboardCorners(gray, (self.chess_width, self.chess_height), None)
        if ret:
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), self.criteria)
            image = cv2.drawChessboardCorners(image, (self.chess_width, self.chess_height), corners2, ret)
        return image

    def capture2(self, left_camera_id, right_camera_id, save_dir):
        """
        Захват видео с двух камер.
        :param left_camera_id: ID первой камеры.
        :param right_camera_id: ID второй камеры.
        :param save_dir: Папка для сохранения кадров.
        """
        self.create_file(save_dir)

        # Инициализация камер с драйвером
        camL = CameraDriver(camera_id=left_camera_id, width=1920, height=1080, flip_horizontal=True, flip_vertical=True)
        camR = CameraDriver(camera_id=right_camera_id, width=1920, height=1080, flip_vertical= True, flip_horizontal=True)

        camL.start_camera()
        camR.start_camera()

        i = 0
        while True:
            frameL = camL.get_frame()
            frameR = camR.get_frame()

            if frameL is None or frameR is None:
                print("Ожидание кадров...")
                time.sleep(0.1)
                continue

            if self.detect:
                l = self.detect_chessboard(frameL.copy())
                r = self.detect_chessboard(frameR.copy())
            else:
                l, r = frameL.copy(), frameR.copy()

            combined = cv2.hconcat([l, r])
            cv2.namedWindow("Dual Cameras", cv2.WINDOW_NORMAL)  # Делаем окно изменяемым
            cv2.resizeWindow("Dual Cameras", 1920, 1080)
            cv2.imshow("Dual Cameras", combined)
            key = cv2.waitKey(10)

            if key == ord('q'):
                break
            elif key in [ord('c'), ord('s')]:
                print(f"Сохранение кадров: {i}")
                cv2.imwrite(os.path.join(save_dir, f"left_{i:03d}.png"), frameL)
                cv2.imwrite(os.path.join(save_dir, f"right_{i:03d}.png"), frameR)
                i += 1

        camL.stop_camera()
        camR.stop_camera()
        cv2.destroyAllWindows()

    @staticmethod
    def create_file(parent_dir):
        """Создание папки, если ее нет."""
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir)

def str2bool(v):
    return v.lower() in ('yes', 'true', 't', 'y', '1')

def get_parser():
    parser = argparse.ArgumentParser(description='Camera calibration')
    parser.add_argument('--width', type=int, default=8, help='Chessboard width size')
    parser.add_argument('--height', type=int, default=11, help='Chessboard height size')
    parser.add_argument('--left_video', type=int, default=0, help='Left camera ID')
    parser.add_argument('--right_video', type=int, default=1, help='Right camera ID')
    parser.add_argument('--detect', type=str2bool, nargs='?', const=True, help='Detect chessboard')
    parser.add_argument('--save_dir', type=str, default="data/camera", help='Save directory')
    return parser

if __name__ == '__main__':
    args = get_parser().parse_args()
    stereo = StereoCamera(args.width, args.height, detect=args.detect)
    stereo.capture2(left_camera_id=args.left_video, right_camera_id=args.right_video, save_dir=args.save_dir)

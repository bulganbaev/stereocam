import cv2
import glob
import os

def create_video(image_pattern, output_video, fps=30):
    """
    Создает видео из изображений, соответствующих шаблону image_pattern.

    :param image_pattern: Шаблон пути к изображениям (например, 'left_*.jpg')
    :param output_video: Имя выходного видеофайла (например, 'left_video.avi')
    :param fps: Частота кадров в секунду
    """
    # Получаем список файлов и сортируем их по имени
    images = sorted(glob.glob(image_pattern))

    if not images:
        print(f"Не найдено изображений для шаблона {image_pattern}")
        return

    # Определяем размер кадра по первому изображению
    frame = cv2.imread(images[0])
    h, w, _ = frame.shape

    # Создаем видео-объект
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    video_writer = cv2.VideoWriter(output_video, fourcc, fps, (w, h))

    for img_path in images:
        frame = cv2.imread(img_path)
        if frame is None:
            print(f"Ошибка загрузки {img_path}, пропускаем")
            continue
        video_writer.write(frame)

    video_writer.release()
    print(f"Видео сохранено: {output_video}")

# Создаем видео из левых и правых изображений
create_video("left_*.jpg", "left_video.avi")
create_video("right_*.jpg", "right_video.avi")

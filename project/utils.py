import cv2
import numpy as np
from fitz import Pixmap


def convert_pixmap_to_ndarray(img: Pixmap) -> np.ndarray:
    image_data = img.samples
    image = np.frombuffer(image_data, dtype=np.uint8).reshape(
        (img.h,
         img.w,
         img.n)
    )
    if img.n == 4:
        image = cv2.cvtColor(image, cv2.COLOR_RGBA2GRAY)
    return image


def show_img(img: np.ndarray):
    cv2.imshow("image", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
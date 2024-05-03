import fitz
import os
import cv2
import numpy as np
from typing import Optional, List
from pylibdmtx.pylibdmtx import decode
import utils


class Decoder:
    def __init__(self):
        self.doc = None
        self.code_a_page = False
        self.page = None
        self.page_pixmap = None

        self.default_page = None
        self.default_page_pixmap = None
        self.page_width = None
        self.page_height = None
        self.area_width = None
        self.area_height = None
        self.rect = None
        self.area_pixmap = None

    def init_doc(self, doc: object) -> None:
        '''
        Задает параметры документа для работы
        с его страницами.
        '''
        os.makedirs(doc.output_dir, exist_ok=True)
        self.doc = doc
        self.default_page = self.doc.pages[0]
        self.default_page_pixmap = self.default_page.get_pixmap()
        self.page_width = self.default_page_pixmap.w
        self.page_height = self.default_page_pixmap.h
        self.area_width = self.doc.selection_end[0] - self.doc.selection_start[0]
        self.area_height = self.doc.selection_end[1] - self.doc.selection_start[1]
        if self.doc.selection_end[0] >= self.page_width or self.doc.selection_end[1] >= self.page_height:
            self.code_a_page = True
        else:
            self.code_a_page = False

    def init_page(self, page_num: int) -> None:
        '''
        Задает параметры страницы для
        декода.
        '''
        self.page = self.doc.pages[page_num]
        self.page_pixmap = self.page.get_pixmap()

    def _move_selection_horizontally(self) -> None:
        '''
        Задает области поиска координаты
        следующего шага слева направо.
        '''
        self.rect.x0 += self.area_width
        self.rect.x1 += self.area_width

    def _go_to_new_line(self) -> None:
        '''
        Задает области поиска координаты
        ночала новой линии.
        '''
        self.rect.x0 = 0
        self.rect.x1 = self.area_width
        self.rect.y0 += self.area_height
        self.rect.y1 += self.area_height

    def _has_black_dot(self, img: np.ndarray, threshold: int = 30) -> np.bool_:
        '''
        Проверяет наличие ерной точки в
        области поиска.
        '''
        if len(img.shape) == 3:
            gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray_img = img
        return np.any(gray_img < threshold)

    def _get_area_pixmap(self) -> fitz.Pixmap:
        '''
        Возвращает pixmap области поиска.
        '''
        matrix = fitz.Matrix(1, 1).prescale(2, 2)
        return self.page.get_pixmap(matrix=matrix, clip=self.rect)

    def _convert_image(self) -> np.ndarray: #TODO: separate
        '''
        Перекодирует pixmap в изображение
        формата, поддерживаемого декодером.
        '''
        image_data = self.area_pixmap.samples
        image = np.frombuffer(image_data, dtype=np.uint8).reshape(
            (self.area_pixmap.h,
             self.area_pixmap.w,
             self.area_pixmap.n)
        )
        if self.area_pixmap.n == 4:
            image = cv2.cvtColor(image, cv2.COLOR_RGBA2GRAY)
        return image

    def _decode_area(self, img: np.ndarray) -> Optional[str|bool]:
        '''
        Ищет изображение с кодом в области поиска.
        Распознает и возвращает строку кода, False
        если нет кода, но есть черная точка, None,
        если область поиска пустая.
        '''
        try:
            decoded_code = decode(img)
            if decoded_code:
                return str(decoded_code[0][0], 'utf-8')
            else:
                if self._has_black_dot(img):
                    return False
        except:
            pass

    def decode_page(self) -> tuple[List[str], bool]:
        local_codes_list = []
        retry = False

        if self.code_a_page:
            self.area_pixmap = self.page_pixmap
            img = utils.convert_pixmap_to_ndarray(self.page_pixmap)
            code = self._decode_area(img)
            if code is not None:
                if not code:
                    retry = True
                local_codes_list.append(code)
        else:
            self.rect = fitz.Rect(0, 0, self.area_width, self.area_height)
            while self.rect.y0 <= self.page_height:
                while self.rect.x0 <= self.page_width:
                    self.area_pixmap = self._get_area_pixmap()
                    img = utils.convert_pixmap_to_ndarray(self.area_pixmap)
                    code = self._decode_area(img)

                    if code is not None:
                        if not code:
                            retry = True
                        else:
                            if local_codes_list:
                                if code != local_codes_list[-1]:
                                    local_codes_list.append(code)
                            else:
                                local_codes_list.append(code)
                    else:
                        break
                    self._move_selection_horizontally()
                self._go_to_new_line()

        return local_codes_list, retry


decoder = Decoder()
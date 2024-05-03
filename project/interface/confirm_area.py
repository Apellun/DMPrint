import cv2
from PySide6 import QtWidgets, QtGui, QtCore
from manager import manager, BaseState


class ConfirmArea(QtWidgets.QDialog):
    area_confirmed_signal = QtCore.Signal(int)
    
    def __init__(self, image, page, parent=None):
        super().__init__(parent)
        self.image = image
        self.page = page

        self.setWindowTitle("Области с кодом")
        self.layout = QtWidgets.QVBoxLayout(self)

        self.label = QtWidgets.QLabel()
        self.continue_button = QtWidgets.QPushButton("Продолжить")
        self.cancel_button = QtWidgets.QPushButton("Выбрать другую область")

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.continue_button)
        self.layout.addWidget(self.cancel_button)

        self.setLayout(self.layout)
        self.continue_button.clicked.connect(self.accept_selection)
        self.cancel_button.clicked.connect(self.select_again)

        self.view_umat()
        self.exec()

    def view_pixmap(self): #pixmap method
        image = QtGui.QImage(self.image.samples, self.image.width, self.image.height, self.image.stride,
                             QtGui.QImage.Format.Format_RGB888)
        self.label.setPixmap(QtGui.QPixmap.fromImage(image))
        self.resize(self.image.width, self.image.height)

    def view_umat(self): #umat method
        np_image = cv2.UMat.get(self.image)

        if len(np_image.shape) == 2:
            height, width = np_image.shape
            bytes_per_line = width
            format_ = QtGui.QImage.Format.Format_Grayscale8
        elif len(np_image.shape) == 3:
            height, width, channels = np_image.shape
            bytes_per_line = 3 * width
            format_ = QtGui.QImage.Format. Format_RGB888

        qimage = QtGui.QImage(np_image.data, width, height, bytes_per_line, format_)
        self.label.setPixmap(QtGui.QPixmap.fromImage(qimage))
        self.resize(width, height)

    def accept_selection(self):
        self.page.set_cropbox(self.page.mediabox)
        manager.base_state = BaseState.DECODE
        self.parent().area_selected()
        self.close()

    def select_again(self):
        self.page.set_cropbox(self.page.mediabox)
        self.close()
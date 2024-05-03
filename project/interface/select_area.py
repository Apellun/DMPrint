import cv2
import fitz
from PySide6 import QtWidgets, QtGui, QtCore
import utils
from manager import manager
from interface.confirm_area import ConfirmArea


class SelectArea(QtWidgets.QDialog):
    area_selected_signal = QtCore.Signal(int)
    cancel_signal = QtCore.Signal()
    
    def __init__(self, page_index=None, parent=None):
        super().__init__(parent)
        self.page_index = page_index

        self.setWindowTitle("Просмотр файла")

        self.label = QtWidgets.QLabel()

        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.label)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.scroll_area)

        self.rubberBand = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Shape.Rectangle, parent=self)

        self.page = None
        self.selection_start = None
        self.selection_end = None
        self.rubber_start = None
        self.rubber_end = None
        self.selected_area_widget = None
        self.pixmap = None

        self.view_pdf()
        self.exec()

    def closeEvent(self, event):
        if event.type() == QtCore.QEvent.Close:
            self.cancel_signal.emit()
            event.accept()
        else:
            event.ignore()
        
    def restore_pixmap(self):
        self.page.set_cropbox(self.page.mediabox)
     
    def area_selected(self):
        if manager.decode_type.value != 0:
            self.parent().process_files()
        self.close()

    def view_pdf(self):
        self.doc = manager.current_doc
        
        if not self.page_index:
            self.page = self.doc.pages[0]
        else:
            self.page = self.doc.pages[self.page_index]
            
        self.pixmap = self.page.get_pixmap()
        image = QtGui.QImage(self.pixmap.samples, self.pixmap.width, self.pixmap.height, self.pixmap.stride,
                             QtGui.QImage.Format.Format_RGB888)
        self.label.setPixmap(QtGui.QPixmap.fromImage(image))
        self.label.resize(self.pixmap.width, self.pixmap.height)
        self.scroll_area.ensureVisible(0, 0)
        self.label.installEventFilter(self)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            selection_start = QtCore.QPoint(self.label.mapFromGlobal(event.globalPos()))
            self.rubber_start = QtCore.QPoint(event.pos())
            self.selection_start = QtCore.QPoint(self.label.mapFromParent(selection_start))

            self.rubberBand.setGeometry(QtCore.QRect(self.rubber_start, QtCore.QSize()))
            self.rubberBand.show()

    def mouseMoveEvent(self, event):
        if self.rubber_start:
            self.rubberBand.setGeometry(QtCore.QRect(self.rubber_start, QtCore.QPoint(event.pos())).normalized())

    def _get_cropped_pixmap(self):
        start_x = self.selection_start.x()
        start_y = self.selection_start.y()
        end_x = self.selection_end.x()
        end_y = self.selection_end.y()

        manager.set_selection_points(start=(start_x, start_y), end=(end_x, end_y))
            
        try:
            self.page.set_cropbox(fitz.Rect(start_x, start_y, end_x, end_y))
            return self.page.get_pixmap()
        except ValueError as e:
            return self.page.get_pixmap()

    def _set_selection(self):
        if self.selection_start.y() > self.selection_end.y():
            start_y = self.selection_end.y()
            end_y = self.selection_start.y()

            self.selection_start.setY(start_y)
            self.selection_end.setY(end_y)

        if self.selection_start.x() > self.selection_end.x():
            start_x = self.selection_end.x()
            end_x = self.selection_start.x()

            self.selection_start.setX(start_x)
            self.selection_end.setX(end_x)

        if self.selection_start.x() < 0:
            adjust_start_x = abs(self.selection_start.x())
            self.selection_start.setX(0)
            self.selection_end.setX(self.selection_end.x() + adjust_start_x)
        if self.selection_start.y() < 0:
            adjust_start_y = abs(self.selection_start.y())
            self.selection_end.setY(self.selection_end.y() + adjust_start_y)
            self.selection_start.setY(0)

        manager.set_selection_points(
            start=(
                self.selection_start.x(),
                self.selection_start.y()
            ),
            end=(
                self.selection_end.x(),
                self.selection_end.y()
            )
        )

    def _get_tile_preview(self) -> cv2.UMat:
        image = cv2.UMat(utils.convert_pixmap_to_ndarray(self.pixmap))

        width = self.selection_end.x() - self.selection_start.x()
        height = self.selection_end.y() - self.selection_start.y()

        start_y = 0
        end_y = height

        while end_y < self.pixmap.height:

            start_x = 0
            end_x = width

            while start_x < self.pixmap.width:
                cv2.rectangle(image, (start_x, start_y), (end_x, end_y), (255, 0, 0), 2)
                start_x += width
                end_x += width

            start_y += height
            end_y += height

        return image

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            selection_end = QtCore.QPoint(self.label.mapFromGlobal(event.globalPos()))
            self.rubber_end = QtCore.QPoint(event.pos())
            self.selection_end = QtCore.QPoint(self.label.mapFromParent(selection_end))

            self._set_selection()

            self.rubberBand.hide()

            tiled_pixmap = self._get_tile_preview()

            self.confirm_area_widget = ConfirmArea(tiled_pixmap, self.page, parent=self) #TODO
            # self.confirm_area_widget.closeEvent = self.restore_pixmap()
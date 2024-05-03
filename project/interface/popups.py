from PySide6.QtWidgets import (QDialog, QLabel, QPushButton,
                               QTextEdit, QWidget, QProgressBar,
                               QVBoxLayout, QHBoxLayout)
from PySide6 import QtCore


class InfoPopup(QDialog):
    def __init__(self, text, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        message_label = QLabel(text)
        layout.addWidget(message_label)

        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, True)
        self.exec()

class RedoPagePopup(QDialog): #TODO: UP
    def __init__(self, len_codes, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Результат")

        layout = QVBoxLayout(self)

        message_label = QLabel(f"Кодов распознано: {len_codes}")
        layout.addWidget(message_label)

        button_layout = QVBoxLayout()
        layout.addLayout(button_layout)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)

        cancel_button = QPushButton("Переделать")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, True)

        self.show()


class RedoDocPopup(QDialog):
    def __init__(self, text, sum_codes=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Результат")
        self.sum_codes = sum_codes

        self.layout = QVBoxLayout(self)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.layout.addWidget(self.text_edit)

        self.create_page_summary()

        first_row_button_layout = QHBoxLayout()
        self.layout.addLayout(first_row_button_layout)

        second_row_button_layout = QHBoxLayout()
        self.layout.addLayout(second_row_button_layout)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        second_row_button_layout.addWidget(ok_button)

        cancel_button = QPushButton("Переделать")
        cancel_button.clicked.connect(self.reject)
        second_row_button_layout.addWidget(cancel_button)

        self.previous_button = QPushButton("<")
        self.previous_button.clicked.connect(self.previous_page)
        first_row_button_layout.addWidget(self.previous_button)

        self.next_button = QPushButton(">")
        self.next_button.clicked.connect(self.next_page)
        first_row_button_layout.addWidget(self.next_button)
        
        # self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, True)
        
        self.set_text(text)
        self.show()

    def create_page_summary(self):
        if self.sum_codes:
            message_label = QLabel(f"Всего кодов распознано: {self.sum_codes}")
            self.layout.addWidget(message_label)
    def set_text(self, text):
        self.pages = self.split_into_pages(text)
        self.current_page = 0
        self.update_display()

    def update_display(self):
        page_text = self.pages[self.current_page]
        self.text_edit.setPlainText(page_text)
        self.update_buttons_state()

    def update_buttons_state(self):
        self.next_button.setEnabled(self.current_page < len(self.pages) - 1)
        self.previous_button.setEnabled(self.current_page > 0)

    def split_into_pages(self, text):
        lines = text.split('\n')
        pages = []
        current_page = []
        for i, line in enumerate(lines, 1):
            current_page.append(line)
            if i % 10 == 0:
                pages.append('\n'.join(current_page))
                current_page = []
        if current_page:
            pages.append('\n'.join(current_page))
        return pages

    def next_page(self):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self.update_display()

    def previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_display()


class ProgressBarPopup(QWidget):
    cancel = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Прогресс")

        self.progress_bar = QProgressBar()
        self.label = QLabel()

        layout = QVBoxLayout(self)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.label)

    def closeEvent(self, event):
        if event.type() == QtCore.QEvent.Close:
            self.cancel.emit()
            event.accept()
        else:
            event.ignore()
        
    def set_progress(self, value):
        self.progress_bar.setValue(value)

    def set_filename(self, value):
        self.label.setText(f"Декодирую {value}")

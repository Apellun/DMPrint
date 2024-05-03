from PySide6 import QtWidgets, QtGui
from PySide6 import QtCore
from functools import partial
from manager import manager, DecodeType, BaseState
from worker import DecodeWorker
from interface.popups import ProgressBarPopup, InfoPopup, RedoDocPopup, RedoPagePopup
from interface.select_area import SelectArea


class RedoInfo(QtWidgets.QDialog):
    area_confirmed_signal = QtCore.Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)

        self.page_index = manager.current_doc.retry_pages[0]
        self.pages_amount = len(manager.current_doc.pages)

        self.page = None
        self.page_pixmap = None

        self.setWindowTitle("Страницы, требующие внимания")

        self.page_codes_label = QtWidgets.QLabel(
            f"Документ: {manager.current_doc.input_file_name}\nНа странице обнаружено кодов: {len(manager.current_doc.codes[self.page_index])}"
        )

        self.page_buttons_layout = QtWidgets.QVBoxLayout()

        self.proceed_button = QtWidgets.QPushButton("Записать коды")
        self.redo_page_button = QtWidgets.QPushButton("Переделать страницу")
        self.redo_doc_button = QtWidgets.QPushButton("Переделать документ")

        self.label = QtWidgets.QLabel()
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.label)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.scroll_area)
        self.layout.addWidget(self.page_codes_label)
        self.layout.addLayout(self.page_buttons_layout)
        self.layout.addWidget(self.proceed_button)
        self.layout.addWidget(self.redo_page_button)
        self.layout.addWidget(self.redo_doc_button)

        self.proceed_button.clicked.connect(self.write_codes)
        self.redo_page_button.clicked.connect(self.redo_page)
        self.redo_doc_button.clicked.connect(self.redo_doc)
        
        self.progress_popup = ProgressBarPopup()
        self.progress_popup.cancel.connect(self.cancel_parsing)
        
        self.worker = DecodeWorker()
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.progress_filename_updated.connect(self.update_filename)
        self.worker.parsing_finished.connect(self.finish_parsing)
        self.worker.parsing_finished.connect(self.cancel_parsing)

        self.create_redo_all_button()
        self.create_page_buttons()
        self.update_page()

        # self.setWindowFlag(QtGui.Qt.WindowStaysOnTopHint, True) #TODO
        
        self.show()
        
    def update_filename(self, value: str):
        self.progress_popup.set_filename(value)
        self.progress_popup.set_progress(0)

    def update_progress(self, value: int):
        self.progress_popup.set_progress(value)
        
    def process_files(self):
        # if manager.base_state == BaseState.DECODE:
        self.worker.start()
        self.progress_popup.show()
        
    def cancel_parsing(self):
        self.worker.terminate()
        #TODO
    
    def finish_parsing(self):
        self.progress_popup.close()
        
        if manager.decode_type.value == 1:
            message = ''
            sum_codes = sum(len(code_list) for code_list in manager.current_doc.codes)
            for i in range(len(manager.current_doc.pages)):
                message += f'\nСтраница {i + 1}: {len(manager.current_doc.codes[i])} кодов'
            redo_doc_popup = RedoDocPopup(message, sum_codes, self)
            if redo_doc_popup.exec():
                InfoPopup("Коды документа сохранены, можно записывать в файл")
            #TODO: cancel option
            self.page_codes_label.setText( #TODO: separate to func
                f"Документ: {manager.current_doc.input_file_name}\nНа странице обнаружено кодов: {len(manager.current_doc.codes[self.page_index])}"
            )
            self.page_codes_label.update()
                
        elif manager.decode_type.value == 2:
            redo_page_popup = RedoPagePopup(len(manager.current_doc.codes[manager.current_page]), self)
            if redo_page_popup.exec():
                InfoPopup("Коды для страницы сохранены, можно записывать в файл")
            self.page_codes_label.setText(
                f"Документ: {manager.current_doc.input_file_name}\nНа странице обнаружено кодов: {len(manager.current_doc.codes[self.page_index])}"
            )
            self.page_codes_label.update()
            #TODO: cancel option
            
        elif manager.decode_type.value == 3:
            message = ''
            for i in range(len(manager.queue)):
                doc_codes = manager.queue[i].codes
                codes_amount = sum([len(page_codes) for page_codes in doc_codes])
                message += f'\nДокумент {i + 1}: {codes_amount}'
            redo_all_popup = RedoDocPopup(message, parent=self)
            if redo_all_popup.exec():
                InfoPopup("Коды документов сохранены, можно записывать в файл")
        
    def display_page(self, index):
        self.page_index = manager.current_doc.retry_pages[index]
        self.update_page()

    def update_page(self):
        if 0 <= self.page_index < self.pages_amount:
            self.page = manager.current_doc.pages[self.page_index]
            if self.page:
                self.page_pixmap = self.page.get_pixmap()
                image = QtGui.QImage(self.page_pixmap.samples, self.page_pixmap.width, self.page_pixmap.height,
                                     self.page_pixmap.stride,
                                     QtGui.QImage.Format.Format_RGB888)
                self.label.setPixmap(QtGui.QPixmap.fromImage(image))
                self.label.resize(self.page_pixmap.width, self.page_pixmap.height)
                self.scroll_area.ensureVisible(0, 0)
                self.page_codes_label.setText(
                    f"Документ: {manager.current_doc.input_file_name}\nНа странице обнаружено кодов: {len(manager.current_doc.codes[self.page_index])}")
                self.page_codes_label.adjustSize()
                
    def update_page_menu(self):
        for i, button in enumerate(self.navigation_buttons):
            page_index = self.button_page_index + i
            if page_index < len(manager.current_doc.retry_pages):
                button.setText(f"Страница {manager.current_doc.retry_pages[page_index] + 1}")
                button.clicked.connect(partial(self.display_page, index=manager.current_doc.retry_pages[page_index]))
                button.setEnabled(True)
            else:
                button.setText("")
                button.setEnabled(False)
                    
    def previous_set(self):
        if self.button_page_index > 0:
            self.button_page_index -= 18
            self.update_page_menu()
            
    def next_set(self):
        if self.button_page_index + 18 < len(manager.current_doc.retry_pages):
            self.button_page_index += 18
            self.update_page_menu()

    def create_page_buttons(self):
        self.navigation_layout = QtWidgets.QGridLayout()
        self.navigation_buttons = []
        
        for row in range(3):
            for col in range(6):
                button = QtWidgets.QPushButton(f"Button {row * 6 + col + 1}")
                self.navigation_layout.addWidget(button, row, col)
                self.navigation_buttons.append(button)
                
        self.page_buttons_layout.addLayout(self.navigation_layout)
        self.button_page_index = 0
        self.update_page_menu()

        button_navigation_layout = QtWidgets.QHBoxLayout()
    
        previous_button = QtWidgets.QPushButton("<")
        previous_button.clicked.connect(self.previous_set)
        button_navigation_layout.addWidget(previous_button)

        next_button = QtWidgets.QPushButton(">")
        next_button.clicked.connect(self.next_set)
        button_navigation_layout.addWidget(next_button)

        self.page_buttons_layout.addLayout(button_navigation_layout)

    def create_redo_all_button(self):
        if manager.one_format:
            redo_all_button = QtWidgets.QPushButton("Переделать все файлы в папке")
            redo_doc_index = self.layout.indexOf(self.redo_doc_button)
            self.layout.insertWidget(redo_doc_index + 1, redo_all_button)
            redo_all_button.clicked.connect(self.redo_all)

    def redo_page(self):
        manager.decode_type = DecodeType(2)
        manager.current_page = self.page_index
        SelectArea(self.page_index, self)
        manager.base_state = BaseState.SELECTING_AREA

    def redo_doc(self):
        manager.decode_type = DecodeType(1)
        SelectArea(parent=self)
        manager.base_state = BaseState.SELECTING_AREA
        
    def redo_all(self):
        manager.decode_type = DecodeType(3)
        SelectArea(parent=self)
        manager.base_state = BaseState.SELECTING_AREA

    def write_codes(self):
        if manager.decode_type.value == 3:
            for doc in manager.queue:
                manager.set_current_doc(doc)
                manager.write_codes()
                manager.finish()
            InfoPopup("Файлы успешно обработаны")
        else:
            manager.write_codes()
            if manager.current_doc is manager.retry_queue[-1]:
                InfoPopup("Файлы успешно обработаны")
                manager.finish()
        
        self.close()
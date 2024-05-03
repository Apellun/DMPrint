import os
from PySide6 import QtCore, QtWidgets
from manager import manager, BaseState
from interface.select_area import SelectArea
from interface.redo_info import RedoInfo
from interface.popups import ProgressBarPopup, InfoPopup
from worker import DecodeWorker


class StartWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Расшифровка DMC")

        grid_layout = QtWidgets.QGridLayout()

        input_dir_label = QtWidgets.QLabel("Папка ввода")
        output_dir_label = QtWidgets.QLabel("Папка вывода")
        select_input_button = QtWidgets.QPushButton("Выбрать папку")
        select_output_button = QtWidgets.QPushButton("Выбрать папку")
        continue_button = QtWidgets.QPushButton("Продолжить")
        self.input_dir_line = QtWidgets.QLineEdit("Папка не выбрана")
        self.output_dir_line = QtWidgets.QLineEdit("Папка не выбрана")
        self.checkbox = QtWidgets.QCheckBox("Документы одного формата")

        grid_layout.addWidget(input_dir_label, 0, 0)
        grid_layout.addWidget(self.input_dir_line, 0, 1)
        grid_layout.addWidget(select_input_button, 0, 2)
        grid_layout.addWidget(output_dir_label, 1, 0)
        grid_layout.addWidget(self.output_dir_line, 1, 1)
        grid_layout.addWidget(select_output_button, 1, 2)
        grid_layout.addWidget(self.checkbox, 2, 1)
        grid_layout.addWidget(continue_button, 2, 2, 1, 2, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)

        select_input_button.clicked.connect(self.select_input_dir)
        select_output_button.clicked.connect(self.select_output_dir)
        continue_button.clicked.connect(self.load_files)

        self.setLayout(grid_layout)

        self.input_dir = None
        self.output_dir = None
        
        self.progress_popup = ProgressBarPopup()
        self.progress_popup.cancel.connect(self.cancel_parsing)

        self.worker = DecodeWorker()
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.progress_filename_updated.connect(self.update_filename)
        self.worker.parsing_finished.connect(self.finish_parsing)

    def update_filename(self, value: str):
        self.progress_popup.set_filename(value)
        self.progress_popup.set_progress(0)

    def update_progress(self, value: int):
        self.progress_popup.set_progress(value)

    def finish_parsing(self):
        self.progress_popup.close()
        manager.base_state = BaseState.INITIAL
        self.process_retry()
    
    def cancel_parsing(self):#TODO: temporary patch
        if not manager.retry_queue:
            if self.worker._is_running:
                self.worker.terminate()
            manager.finish()

    def select_input_dir(self):
        dir_name = QtWidgets.QFileDialog.getExistingDirectory()
        if dir_name:
            self.input_dir_line.setText(dir_name)
            self.input_dir = dir_name

    def select_output_dir(self):
        dir_name = QtWidgets.QFileDialog.getExistingDirectory()
        if dir_name:
            self.output_dir_line.setText(dir_name)
            self.output_dir = dir_name

    def select_area(self):
        manager.form_queue()

        if not manager.one_format:
            for doc in manager.queue:
                manager.set_current_doc(doc)
                manager.base_state = BaseState.SELECTING_AREA
                self.select_area_widget = SelectArea(parent=self)
                self.select_area_widget.cancel_signal.connect(self.cancel_parsing)
        else:
            manager.set_current_doc()
            manager.base_state = BaseState.SELECTING_AREA
            self.select_area_widget = SelectArea(parent=self)
            self.select_area_widget.cancel_signal.connect(self.cancel_parsing)

        self.process_files()
    
    def process_files(self):
        if manager.base_state == BaseState.DECODE:
            self.worker.start()
            self.progress_popup.show()
        
    def process_retry(self):
        if manager.retry_queue:
            i = 0
            while i < len(manager.retry_queue):
                manager.base_state = BaseState.INITIAL
                manager.set_current_doc(manager.retry_queue[i])
                self.redo_info_widget = RedoInfo(parent=self)
                self.redo_info_widget.exec_()
                i += 1
                if manager.decode_type.value == 3:
                    break
        else:
            InfoPopup("Файлы успешно обработаны")
            manager.finish()

    def load_files(self):
        manager.finish()
        if self.input_dir and self.output_dir:
            pdf_files = [file for file in os.listdir(self.input_dir) if file.endswith(".pdf")]
            if pdf_files:
                manager.set_dirs(self.input_dir, self.output_dir)
                if self.checkbox.isChecked():
                    manager.one_format = True
                    manager.docs = pdf_files
                else:
                    manager.docs = pdf_files
            else:
                InfoPopup("В выбранной папке нет pdf-файлов")
                return
        else:
            InfoPopup("Папки не выбраны")
            return
            
        self.select_area()
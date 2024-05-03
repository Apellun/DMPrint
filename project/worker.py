from PySide6 import QtCore
from manager import manager
from decoder import decoder


class DecodeWorker(QtCore.QThread):
    progress_updated = QtCore.Signal(int)
    progress_filename_updated = QtCore.Signal(str)
    parsing_finished = QtCore.Signal()

    def __init__(self):
        QtCore.QThread.__init__(self)
        self.setTerminationEnabled(True)
        self._is_running = True

    def stop(self) -> None:
        self._is_running = False

    def run(self) -> None:
        if manager.decode_type.value == 0 or manager.decode_type.value == 3:
            for doc in manager.queue:
                
                if manager.one_format:
                    manager.set_current_doc(doc)
                    
                print(f"parsing {doc.input_file_path}")

                decoder.init_doc(doc)
                manager.set_current_doc(doc)
                
                self.progress_filename_updated.emit(doc.input_file_name)
                doc_codes = []
                retry_pages = []
                local_codes_counter = 0
                
                pages_amount = len(manager.current_doc.pages)

                for page_num in range(pages_amount):
                    print(f"parsing page {page_num + 1}")

                    decoder.init_page(page_num)
                    page_codes, retry = decoder.decode_page()

                    progress = int((page_num / pages_amount) * 100)
                    self.progress_updated.emit(progress)

                    if retry:
                        retry_pages.append(page_num)
                    elif page_num == 0:
                        local_codes_counter = len(page_codes)
                    elif local_codes_counter != len(page_codes):
                        retry_pages.append(page_num)

                    doc_codes.append(page_codes)
                    page_num += 1

                print(f"finished parsing {doc.input_file_path}")
                
                doc.codes = doc_codes
                
                if retry_pages:
                    doc.retry_pages = retry_pages
                    if not manager.retry_queue:
                        manager.retry_queue = []
                    manager.retry_queue.append(doc)
                else:
                    if manager.decode_type.value == 0: #TODO: gather writing in one place
                        manager.write_codes()
                
            self.parsing_finished.emit()
            print(f"finished parsing")
        else:
            decoder.init_doc(manager.current_doc)

            if manager.decode_type.value == 2:
                print("redoing page")
                
                decoder.init_page(manager.current_page)

                self.progress_filename_updated.emit(f"страницу {manager.current_page + 1}")

                print(f"parsing page {manager.current_page + 1}")
                page_codes, retry = decoder.decode_page()
                print(f"finished parsing")

                manager.current_doc.codes[manager.current_page] = page_codes

            elif manager.decode_type.value == 1:
                print("redoing doc")
                
                doc_codes = []
                self.progress_filename_updated.emit(manager.current_doc.input_file_name)
                pages_amount = len(manager.current_doc.pages)

                for page_num in range(pages_amount):
                    print(f"parsing page {page_num}")
                    
                    decoder.init_page(page_num)
                    page_codes, retry = decoder.decode_page()

                    progress = int((page_num / pages_amount) * 100)
                    self.progress_updated.emit(progress)

                    doc_codes.append(page_codes)
                    page_num += 1
                    
                    manager.current_doc.codes = doc_codes
                    
                print(f"finished parsing {manager.current_doc.input_file_path}")
            
            self.parsing_finished.emit()
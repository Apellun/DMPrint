import fitz
from typing import List
from enum import Enum
from document import Document


class BaseState(Enum):
    INITIAL = 0
    SELECTING_AREA = 1
    DECODE = 2
    
    
class DecodeType(Enum):
    INITIAL = 0
    REDO_DOC = 1
    REDO_PAGE = 2
    REDO_ALL = 3


class Manager:
    def __init__(self):
        self.base_state = BaseState.INITIAL
        self.decode_type = BaseState.INITIAL
        
        self.one_format: bool = False

        self.input_dir: str = None
        self.output_dir: str = None

        self.queue: List[Document] = None
        self.retry_queue: List[Document] = None
        self.docs: List[str] = None

        self.current_doc: Document = None
        self.current_page: int = None

    def _init_doc(self, doc: str) -> Document:
        document = Document()
        document.input_dir = self.input_dir
        document.output_dir = self.output_dir
        document.input_file_name = doc
        document.output_file_name = doc.replace("pdf", "csv")
        document.input_file_path = self.input_dir + "/" + doc
        document.output_file_path = self.output_dir + "/" + document.output_file_name
        document.opened = fitz.open(document.input_file_path)
        document.pages = [page for page in document.opened]
        document.retry_pages = None
        return document

    def set_dirs(self, input_dir: str, output_dir: str) -> None:
        self.input_dir = input_dir
        self.output_dir = output_dir

    def form_queue(self) -> None:
        self.queue = []
        for doc in self.docs:
            document = self._init_doc(doc)
            self.queue.append(document)

    def set_current_doc(self, doc: fitz.Document = None) -> None:
        if doc:
            self.current_doc = doc
        else:
            self.current_doc = self.queue[0]

    def set_selection_points(self, start: tuple[int, int], end: tuple[int, int]) -> None:
        if not self.one_format:
            self.current_doc.selection_start = start
            self.current_doc.selection_end = end
        else:
            for doc in self.queue:
                doc.selection_start = start
                doc.selection_end = end

    def write_codes(self) -> None:
        with open(self.current_doc.output_file_path, 'a', encoding="utf-8") as f:
            for code_list in self.current_doc.codes:
                for code in code_list:
                    f.write(f"{code}\n")
                    
    def finish(self):
        self.base_state = BaseState.INITIAL
        self.decode_type = DecodeType.INITIAL
        self.one_format = False
        self.current_doc = None
        self.current_page = None
        
        try:
            for doc in self.queue:
                doc.opened.close()
            if self.retry_queue:
                for doc in self.retry_queue:
                    doc.opened.close()
        except:
            pass
                
        self.queue = []
        self.retry_queue = []


manager = Manager()
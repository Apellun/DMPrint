from dataclasses import dataclass
from typing import List
from PySide6 import QtCore
from fitz import Document


@dataclass
class Document:
    input_dir: str = None
    output_dir: str = None
    input_file_name: str = None
    output_file_name: str = None
    input_file_path: str = None
    output_file_path: str = None

    opened: Document = None

    selection_start: QtCore.QPoint = None
    selection_end: QtCore.QPoint = None

    pages: List = None
    retry_pages: List = None
    codes: List = None
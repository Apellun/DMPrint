import sys
from PySide6 import QtWidgets
from interface.start_window import StartWindow
from interface.popups import InfoPopup


def main():
    app = QtWidgets.QApplication([])

    widget = StartWindow()
    widget.resize(400, 200)
    widget.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        InfoPopup(f"Ошибка: {e}")

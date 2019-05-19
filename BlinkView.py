import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton


class BlinkView(QWidget):
    def __init__(self):
        super().__init__()
        self.title = 'blink'
        self.left = 10
        self.top = 10
        self.width = 320
        self.height = 200
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        full_scan_button = QPushButton('Full Scan', self)
        full_scan_button.move(50, 60)
        partial_scan_button = QPushButton('Partial Scan', self)
        partial_scan_button.move(150, 60)
        full_scan_button.clicked.connect(lambda x: print('clicked'))
        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = BlinkView()
    sys.exit(app.exec_())


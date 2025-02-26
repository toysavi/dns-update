import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QFileDialog
from PyQt5.QtCore import Qt

class DNSUpdaterApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('DNS Updater')
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon('img/icon.ico'))  # Set the icon

        # GUI Layout and Elements
        self.init_ui()

    def init_ui(self):
        # Define layout and buttons
        layout = QVBoxLayout()

        # Example of adding a button
        self.import_btn = QPushButton('Import CSV')
        self.import_btn.clicked.connect(self.import_csv)

        # Adding button to layout
        layout.addWidget(self.import_btn)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def import_csv(self):
        file, _ = QFileDialog.getOpenFileName(self, 'Open CSV', '', 'CSV Files (*.csv)')
        if file:
            print(f'CSV File Imported: {file}')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DNSUpdaterApp()
    window.show()
    sys.exit(app.exec_())

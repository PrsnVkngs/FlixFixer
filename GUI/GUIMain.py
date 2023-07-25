from pathlib import Path

from PyQt6.QtWidgets import QApplication, QFileDialog, QPushButton, QVBoxLayout, QWidget

from MovieDatabase import MovieDatabase


class MovieDatabaseApp(QWidget):
    def __init__(self, db: MovieDatabase):
        super().__init__()
        self.add_dir_button = QPushButton("Add Directory", self)
        self.db = db
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.add_dir_button.clicked.connect(self.add_directory)  # connect the button click event to add_directory

        layout.addWidget(self.add_dir_button)
        self.setLayout(layout)

    def add_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")  # prompt user to choose a directory
        if dir_path:  # if user did not cancel the dialog
            self.db.add_directory(Path(dir_path), recursive=True)  # add the directory to the database

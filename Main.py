import sys

from PyQt6.QtWidgets import QApplication

from MovieDatabase import MovieDatabase
from main_view import MainWindow

app = QApplication([])
connection_string = 'mongodb://localhost:27017'
m_db = MovieDatabase(connection_string, "movie_database")
window = MainWindow(m_db)
window.show()
sys.exit(app.exec())

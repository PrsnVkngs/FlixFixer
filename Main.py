import sys
import asyncio

from PyQt6.QtWidgets import QApplication

from MovieDatabase import MovieDatabase
from main_view import MainWindow

from Concurrency.ConcurrentRequests import ConcurrentRequests


def load_stylesheet(filename: str) -> str:
    with open(filename, "r") as f:
        return f.read()


async def main():
    app = QApplication([])
    app.setStyleSheet(load_stylesheet("GUI\\style.qss"))  # TODO add style to the program later
    connection_string = 'mongodb://localhost:27017'
    concurrent_requests = ConcurrentRequests()
    m_db = MovieDatabase(connection_string, "movie_database", concurrent_requests)
    window = MainWindow(m_db)
    window.show()
    return_code = app.exec()
    await concurrent_requests.close()
    sys.exit(return_code)


if __name__ == "__main__":
    asyncio.run(main())

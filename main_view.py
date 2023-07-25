from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (QSplitter, QListWidget, QLabel,
                             QVBoxLayout, QHBoxLayout, QWidget, QTabWidget, QFileDialog,
                             QPushButton, QLineEdit, QComboBox, QListWidgetItem,
                             QTreeWidgetItem, QTreeWidget, QHeaderView, QAbstractItemView, QDialog, QSpinBox,
                             QScrollArea, QFormLayout)

from GUI.DirectoryDialog import RecursiveDialog
from InformationGrabbers.get_tmdb_data import make_tmdb_call
from MovieDatabase import MovieDatabase
from InformationGrabbers.file_info import get_movies_from_directory
from MovieDatabase import MovieInfo

import cProfile
import pstats
import webbrowser


class MainWindow(QWidget):
    directoriesSignal = pyqtSignal(list)

    def __init__(self, db: MovieDatabase):
        super().__init__()
        self.db = db

        self.movie_display_settings = {
            MovieInfo.ADULT: False,
            MovieInfo.BACKDROP: False,
            MovieInfo.POSTER: True,
            MovieInfo.COLLECTION: False,
            MovieInfo.BUDGET: False,
            MovieInfo.GENRES: True,
            MovieInfo.HOMEPAGE: False,
            MovieInfo.TMDB_ID: True,
            MovieInfo.IMDB_ID: False,
            MovieInfo.LANGUAGE: False,
            MovieInfo.TITLE_ORIG: True,
            MovieInfo.TITLE_CUR: False,
            MovieInfo.OVERVIEW: True,
            MovieInfo.POPULARITY: False,
            MovieInfo.PRODUCTION_COMPANY: False,
            MovieInfo.PRODUCTION_COUNTRY: False,
            MovieInfo.RELEASE: False,
            MovieInfo.REVENUE: False,
            MovieInfo.RUNTIME: True,
            MovieInfo.LANGUAGES: False,
            MovieInfo.STATUS: False,
            MovieInfo.TAGLINE: True,
            MovieInfo.RATING: True,
            MovieInfo.RATERS: True
        }

        self.movie_display_objects = None

        self.filterComboBox = None
        self.searchBar = None
        self.directoryList = None  # list of directories in the directory page.
        self.settingsTab = None
        self.movieInfo = None
        self.mainTab = None
        self.movieList = None  # list of movies in the main page.
        self.plotLabel = None
        self.posterLabel = None
        self.titleLabel = None
        self.taglineLabel = None
        self.cast_widget = None
        self.cast_scroll = None
        self.movie_info_widget = None
        self.movie_info_scroll = None
        self.images_location = None
        self.images_location_button = None
        self.settings_file_location_button = None
        self.settings_file_location = None
        self.setWindowTitle('Movie Viewer')
        self.setGeometry(500, 500, 550, 350)

        self.settings_path = ''
        self.images_path = ''

        self.settings_path = self.db.read_config('settings_location')
        while self.settings_path is None:
            self.settings_path = QFileDialog.getExistingDirectory(self, 'Select Settings Directory')
        self.db.set_config('settings_location', self.settings_path)

        self.images_path = self.db.read_config('images_location')
        while self.images_path is None:
            self.images_path = QFileDialog.getExistingDirectory(self, 'Select Image Directory')
        self.db.set_config('images_location', self.images_path)
        self.db.images_directory = Path(self.images_path)

        self.tabWidget = QTabWidget()

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.tabWidget)

        self.setLayout(layout)

        # Create tabs
        self.create_main_tab()
        self.create_directory_tab()
        self.create_settings_tab()

    def create_main_tab(self):
        self.mainTab = QWidget()
        self.tabWidget.addTab(self.mainTab, "Main")

        self.movieList = QListWidget()
        self.movieList.itemClicked.connect(self.show_movie_info)

        self.movieInfo = QWidget()
        main_layout = QVBoxLayout()

        # Title
        self.titleLabel = QLabel("Title")
        self.titleLabel.setFont(QFont('Arial', 24))
        main_layout.addWidget(self.titleLabel)

        # Poster, tagline, and plot
        poster_tagline_layout = QHBoxLayout()

        self.posterLabel = QLabel("Poster")  # Should display an image
        poster_tagline_layout.addWidget(self.posterLabel)

        self.taglineLabel = QLabel("Tagline")
        self.plotLabel = QLabel("Plot")

        tagline_plot_layout = QVBoxLayout()
        tagline_plot_layout.addWidget(self.taglineLabel)
        tagline_plot_layout.addWidget(self.plotLabel)

        poster_tagline_layout.addLayout(tagline_plot_layout)
        main_layout.addLayout(poster_tagline_layout)

        # Other movie info and cast
        info_cast_layout = QVBoxLayout()

        self.movie_info_scroll = QScrollArea()
        self.movie_info_widget = QWidget()  # Populate with movie info widgets
        self.movie_info_scroll.setWidget(self.movie_info_widget)
        self.movie_info_scroll.setWidgetResizable(True)
        info_cast_layout.addWidget(self.movie_info_scroll)

        self.cast_scroll = QScrollArea()
        self.cast_widget = QWidget()  # Populate with cast widgets (e.g., QLabels with images and text)
        self.cast_scroll.setWidget(self.cast_widget)
        self.cast_scroll.setWidgetResizable(True)
        info_cast_layout.addWidget(self.cast_scroll)

        main_layout.addLayout(info_cast_layout)

        self.movieInfo.setLayout(main_layout)

        info_scroll = QScrollArea()
        info_scroll.setWidgetResizable(True)
        info_scroll.setWidget(self.movieInfo)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.movieList)
        splitter.addWidget(info_scroll)

        tab_layout = QVBoxLayout()
        tab_layout.addWidget(splitter)
        tab_layout.addLayout(self.create_bottom_bar())

        self.mainTab.setLayout(tab_layout)

        self.populate_movie_list()

    def create_directory_tab(self):
        self.settingsTab = QWidget()
        self.tabWidget.addTab(self.settingsTab, "Directories")

        self.directoryList = DirectoryTree()
        self.directoryList.setDragDropMode(self.directoryList.DragDropMode.InternalMove)
        self.directoryList.requestDirectoriesSignal.connect(self.handle_directories_request)
        self.directoryList.addDirectorySignal.connect(self.add_directory_to_db)
        # self.directoryList.dropEvent = self.dropEvent
        self.directoriesSignal.connect(self.directoryList.receive_list)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Indexed Directories"))
        layout.addWidget(self.directoryList)
        layout.addLayout(self.create_directory_buttons())

        self.settingsTab.setLayout(layout)

        self.directoryList.populate_directory_list(self.db.get_directories())

    def create_directory_buttons(self):
        layout = QHBoxLayout()

        add_button = QPushButton("Add Directory")
        add_button.clicked.connect(self.add_directory_to_db)
        delete_button = QPushButton("Delete Directory")
        delete_button.clicked.connect(self.remove_directory_from_db)

        layout.addWidget(add_button)
        layout.addWidget(delete_button)

        return layout

    def create_bottom_bar(self):
        layout = QHBoxLayout()

        self.searchBar = QLineEdit()
        self.searchBar.setPlaceholderText("Search for a movie...")

        self.filterComboBox = QComboBox()
        self.filterComboBox.addItems(["Filter by...", "Starts with...", "Genre..."])

        layout.addWidget(self.searchBar)
        layout.addWidget(self.filterComboBox)

        return layout

    def create_settings_tab(self):
        self.settingsTab = QWidget()
        self.tabWidget.addTab(self.settingsTab, "Settings")

        settings_layout = QFormLayout()

        self.settings_file_location = QLineEdit(self)
        self.settings_file_location.setText(self.settings_path)
        self.settings_file_location_button = QPushButton('Browse', self)
        self.settings_file_location_button.clicked.connect(self.browse_for_settings_file)

        settings_layout.addRow('Settings File Location:', self.settings_file_location)
        settings_layout.addRow('', self.settings_file_location_button)

        self.images_location = QLineEdit(self)
        self.images_location.setText(self.images_path)
        self.images_location_button = QPushButton('Browse', self)
        self.images_location_button.clicked.connect(self.browse_for_images)

        settings_layout.addRow('Images Location:', self.images_location)
        settings_layout.addRow('', self.images_location_button)

        self.settingsTab.setLayout(settings_layout)

    def browse_for_settings_file(self):
        file_name = QFileDialog.getOpenFileName(self, 'Select Settings Folder')
        if file_name:
            self.settings_file_location.setText(file_name)
            self.db.set_config('settings_location', file_name)
            self.db.settings_path = file_name

    def browse_for_images(self):
        directory = QFileDialog.getExistingDirectory(self, 'Select Image Directory')
        if directory:
            self.images_location.setText(directory)
            self.db.set_config('images_location', directory)
            self.db.images_directory = directory

    def add_directory_to_db(self, dir_path: Path = None):
        if not dir_path:
            dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")  # prompt user to choose a directory
        if dir_path:  # if user did not cancel the dialog
            dialog = RecursiveDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                recursive, recursion_depth = dialog.get_values()
                self.db.add_directory(Path(dir_path), recursive=recursive,
                                      depth=recursion_depth)  # add the directory to the database
                self.directoryList.populate_directory_list(self.db.get_directories())
                self.populate_movie_list()

    def remove_directory_from_db(self):
        current_item = self.directoryList.get_selected_dir()
        if current_item:
            # Delete directory from file
            self.db.remove_directory(Path(current_item))
            self.directoryList.populate_directory_list(self.db.get_directories())
            self.populate_movie_list()

    def handle_directories_request(self):
        directories = self.db.get_directories()
        self.directoriesSignal.emit(directories)

    def populate_movie_list(self):
        # Clear list first
        self.movieList.clear()

        # profiler = cProfile.Profile()
        # profiler.enable()

        dirs = self.db.get_directories()
        if dirs:
            for mov_dir in dirs:  # TODO later down the line, add in checks if the user has added a directory down the recursion line.
                # assuming get_movie_files is a function that retrieves .mkv files from a directory
                movies = get_movies_from_directory(Path(mov_dir['path']), mov_dir['depth'])
                for movie in movies:
                    self.movieList.addItem(str(movie.name))
                    self.db.add_movie(movie)

        # profiler.disable()
        #
        # # Generate profiling report
        # stats = pstats.Stats(profiler)
        # stats.sort_stats(pstats.SortKey.TIME)  # Sort the report by time spent
        # stats.print_stats()  # Print the profiling report
        #
        # # Generate graphical visualization and open it in the default web browser
        # stats.dump_stats('profile_results.prof')  # Save profiling data
        # webbrowser.open('profile_results.prof')  # Open the visualization in the web browser

    def show_movie_info(self, item):
        movie = item.text()
        print(movie)
        # assuming make_tmdb_call is a function that retrieves a movie info from TMDb
        # info = make_tmdb_call(movie)  # more complicated as we need to add elements that will show us what we want.
        # self.movieInfo.setText(movie)  # TODO need to change to populate with movie info.


class DirectoryItem(QTreeWidgetItem):
    def __init__(self, parent=None, recurse=None, spin_box_value=None):
        super().__init__(parent)
        self.setFlags(self.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        self.setCheckState(1, recurse)

        # Create a QSpinBox
        spin_box = QSpinBox()
        spin_box.setMinimum(0)
        spin_box.setMaximum(100)
        spin_box.setValue(spin_box_value)
        # Set the QSpinBox as the data of the second column (index 2)
        self.setData(2, Qt.ItemDataRole.UserRole, spin_box)

    def get_dir(self):
        return self.text(0)


class DirectoryTree(QTreeWidget):
    requestDirectoriesSignal = pyqtSignal()
    addDirectorySignal = pyqtSignal(Path)
    directoryResult = []

    def __init__(self, parent=None):
        super(DirectoryTree, self).__init__(parent)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)
        self.setDefaultDropAction(Qt.DropAction.CopyAction)
        self.setHeaderLabels(["Directory", "Recursive", "Depth"])
        self.header().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                print(url)
                path = url.toLocalFile()
                print(path, type(path))
                self.addDirectorySignal.emit(Path(path))
            self.clear()
            self.populate_directory_list()
            event.acceptProposedAction()

    def request_directories(self):
        self.requestDirectoriesSignal.emit()

    def populate_directory_list(self, dirs: list[dict] = None):
        self.clear()
        if not dirs:
            self.request_directories()
            dirs = self.directoryResult
        if dirs:
            for dir in dirs:
                recrs = Qt.CheckState.Unchecked
                if dir['recursive']:
                    recrs = Qt.CheckState.Checked
                item = DirectoryItem(self, recurse=recrs, spin_box_value=dir['depth'])
                item.setText(0, str(Path(dir['path'])))

    def receive_list(self, directories):
        """
        This function is responsible for receiving the directories from the main class.
        :param directories:
        :return:
        """
        self.directoryResult = directories

    def get_selected_dir(self):
        return self.currentItem().text(0)

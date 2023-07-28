from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import (QSplitter, QListWidget, QLabel,
                             QVBoxLayout, QHBoxLayout, QWidget, QTabWidget, QFileDialog,
                             QPushButton, QLineEdit, QComboBox, QTreeWidgetItem, QTreeWidget, QHeaderView, QAbstractItemView, QDialog, QSpinBox,
                             QScrollArea, QFormLayout, QSizePolicy)

from GUI.CastItem import CastItem
from GUI.DirectoryDialog import RecursiveDialog
from MovieDatabase import MovieDatabase, Cast
from InformationGrabbers.file_info import get_movies_from_directory
from MovieDatabase import MovieInfo
from GUI.InfoScrollers import create_info_scroller_layout

CAST_WIDGET_COUNT = 100


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
            MovieInfo.PLOT: True,
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
        self.titleLabel = QLabel()
        self.taglineLabel = None
        self.cast_widget = None
        self.cast_scroll = None
        self.movie_info_widget = None
        self.movie_info_scroll = None
        self.images_location = None
        self.images_location_button = None
        self.settings_file_location_button = None
        self.settings_file_location = None

        self.info_scroller_references = None
        self.cast_scroll_layout = None
        self.cast_widget_items = [CastItem() for _ in range(CAST_WIDGET_COUNT)]  # create CAST_WIDGET_COUNT number of CastItem objects

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

        poster_layout = QVBoxLayout()
        self.posterLabel = QLabel("Poster")  # Should display an image
        self.posterLabel.setScaledContents(True)
        self.posterLabel.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.posterLabel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        poster_layout.addWidget(self.posterLabel)

        poster_tagline_layout.addLayout(poster_layout, 1)

        tagline_plot_layout = QVBoxLayout()
        self.taglineLabel = QLabel("Tagline")
        self.taglineLabel.setWordWrap(True)
        self.plotLabel = QLabel("Plot")
        self.plotLabel.setWordWrap(True)
        tagline_plot_layout.addWidget(self.taglineLabel)
        tagline_plot_layout.addWidget(self.plotLabel)

        poster_tagline_layout.addLayout(tagline_plot_layout, 3)

        main_layout.addLayout(poster_tagline_layout)

        # Other movie info and cast
        info_cast_layout = QVBoxLayout()

        self.movie_info_scroll = QScrollArea()
        self.movie_info_widget = QWidget()  # Populate with movie info widgets
        self.movie_info_widget.setToolTip('Movie Info')
        scroller_layout, self.info_scroller_references = create_info_scroller_layout(self.movie_display_settings)
        self.movie_info_widget.setLayout(scroller_layout)
        self.movie_info_scroll.setWidget(self.movie_info_widget)
        self.movie_info_scroll.setWidgetResizable(True)
        info_cast_layout.addWidget(self.movie_info_scroll)

        self.cast_scroll = QScrollArea()
        self.cast_widget = QWidget()  # Populate with cast widgets (e.g., QLabels with images and text)
        self.cast_widget.setToolTip('Cast')
        # we can include pre-defined cast objects here after we determine performance impacts.
        self.cast_scroll_layout = QHBoxLayout()
        for each in self.cast_widget_items:
            each.setVisible(False)
            self.cast_scroll_layout.addWidget(each)
        self.cast_widget.setLayout(self.cast_scroll_layout)
        self.cast_scroll.setWidget(self.cast_widget)
        self.cast_scroll.setWidgetResizable(True)
        info_cast_layout.addWidget(self.cast_scroll)

        main_layout.addLayout(info_cast_layout)

        self.movieInfo.setLayout(main_layout)

        # info_scroll = QScrollArea()
        # info_scroll.setWidgetResizable(True)
        # info_scroll.setWidget(self.movieInfo)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.movieList)
        splitter.addWidget(self.movieInfo)

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
        file_name = QFileDialog.getExistingDirectory(self, 'Select Settings Folder')
        print(file_name)
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

        # Get the movie info
        movie_info = self.db.get_movie(movie)

        if not movie_info:
            print(f"No information found for movie {movie}")
            return

        # Get the misc_info sub-dictionary, which contains most of the relevant fields
        misc_info = movie_info.get("misc_info", {})

        # set title
        self.titleLabel.setText(misc_info.get(MovieInfo.TITLE_CUR.value))
        # end setting title

        # set poster image
        image_paths = self.db.get_images(movie).get('images')
        poster_path = None
        if image_paths is not None:
            poster_path = image_paths.get(MovieInfo.POSTER.value)
        if poster_path is not None:
            pixmap = QPixmap(poster_path)
            pixmap = pixmap.scaled(self.posterLabel.width(), self.posterLabel.height(),
                                   aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatioByExpanding)
            self.posterLabel.setPixmap(pixmap)
        # end setting poster image

        # set the tagline and plot
        self.taglineLabel.setText(misc_info.get(MovieInfo.TAGLINE.value))
        self.plotLabel.setText(misc_info.get(MovieInfo.PLOT.value))
        # end setting tagline and plot

        # set info scroller text
        for info_enum, gui_label in self.info_scroller_references.items():
            gui_label.setText(f"{info_enum.name}: {misc_info.get(info_enum.value)}")

        # end setting info scroller text

        # set cast info

        cast_info = movie_info.get('cast')
        for i in range(100):
            if i < len(cast_info):
                cast_id, character_name = cast_info[i]
                member_info = self.db.get_cast_member(cast_id)
                self.cast_widget_items[i].update_info(member_info[Cast.NAME_NOW], character_name, member_info[Cast.HEADSHOT])
                self.cast_widget_items[i].setVisible(True)
            else:
                self.cast_widget_items[i].setVisible(False)

        # end setting cast


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

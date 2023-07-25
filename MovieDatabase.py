import pathlib
from io import BytesIO
from pathlib import Path
import configparser
import requests
from PIL import Image

from enum import Enum

from pymongo import MongoClient

from InformationGrabbers.file_info import get_res_codec
from InformationGrabbers.get_tmdb_data import get_tmdb_id, make_tmdb_call, compile_cast
from InformationGrabbers.metadata import get_track_info


class MovieInfo(str, Enum):
    """
    Enumeration for the details that are inside a tmdb call, in an easy to access format. No need to reference TMDB API
    all the time.
    """
    ADULT = 'adult'
    BACKDROP = 'backdrop_path'
    POSTER = 'poster_path'
    COLLECTION = 'belongs_to_collection'
    BUDGET = 'budget'
    GENRES = 'genres'
    HOMEPAGE = 'homepage'
    TMDB_ID = 'id'
    IMDB_ID = 'imdb_id'
    LANGUAGE = 'original_language'
    TITLE_ORIG = 'original_title'
    TITLE_CUR = 'title'
    OVERVIEW = 'overview'
    POPULARITY = 'popularity'
    PRODUCTION_COMPANY = 'production_companies'
    PRODUCTION_COUNTRY = 'production_countries'
    RELEASE = 'release_date'
    REVENUE = 'revenue'
    RUNTIME = 'runtime'
    LANGUAGES = 'spoken_languages'
    STATUS = 'status'
    TAGLINE = 'tagline'
    RATING = 'vote_average'
    RATERS = 'vote_count'


# COLLECTION_ID = 'id'
# COLLECTION_NAME = 'name'
# COLLECTION_POSTER = 'poster_path'
# COLLECTION_BACKDROP = 'backdrop_path'

class InternalInfo(str, Enum):
    NAME_OF_COLLECTION = 'collection_name'
    ACTORS = 'actors'
    RESOLUTION = 'v_resolution'
    CODEC = 'a_codec'


class DatabaseEntry(str, Enum):
    ENTRY_KEY = '_id'
    DIRECTORY_KEY = 'directory_id'
    MISC_INFO = 'misc_info'
    METADATA = 'metadata'
    AUDIO = InternalInfo.CODEC
    VIDEO = InternalInfo.RESOLUTION
    CAST = 'cast'


# class Images(Enum):
#     MOVIE_POSTER = MovieInfo.POSTER
#     MOVIE_BACKDROP =

keyable_info = (MovieInfo.ADULT, MovieInfo.GENRES)

searchable_info = (MovieInfo.ADULT, MovieInfo.GENRES, InternalInfo.RESOLUTION, InternalInfo.CODEC)


class MovieDatabase:
    def __init__(self, db_url, db_name):
        client = MongoClient(db_url)
        self.db = client[db_name]
        self.movies = self.db['movies']
        self.directories = self.db['directories']
        self.images = self.db['images']

        self.config = configparser.ConfigParser()
        self.settings_path = None
        self.images_directory = None

    def add_directory(self, dir_path: pathlib.Path = None, recursive: bool = False, depth: int = None):
        if not dir_path:
            return
        data = {
            "path": str(dir_path.absolute()),
            "recursive": recursive,
            "depth": depth
        }
        self.directories.insert_one(data)
        # TODO can change this to update and check the return value to see if the directory exists.

    def remove_directory(self, dir_path: pathlib.Path = None):
        if dir_path:
            print(dir_path.parts)
            self.directories.delete_one({"path": str(dir_path.absolute())})

    def get_directories(self) -> list[dict]:
        return list(self.directories.find({}))

    def add_movie(self, file_path: Path, force_update: bool = False):
        tmdb_id = get_tmdb_id(file_path)
        if self.movies.find_one({'_id': tmdb_id}) and not force_update:
            return

        # Extract TMDB ID and other metadata from the file
        media_info = get_track_info(file_path)
        if tmdb_id:
            movie_info = make_tmdb_call(tmdb_id)
        else:
            movie_info = make_tmdb_call(str(file_path.name))
            tmdb_id = movie_info['id']

        resolution, a_codec = get_res_codec(file_path)

        image_paths = {
            MovieInfo.POSTER.value: movie_info.pop(MovieInfo.POSTER.value),
            MovieInfo.BACKDROP.value: movie_info.pop(MovieInfo.BACKDROP.value)
        }

        self.insert_images(tmdb_id, image_paths)

        cast = compile_cast(tmdb_id)

        # Get directory document
        directory = self.directories.find_one({"path": str(file_path.parent.absolute())})

        # Merge the file info, movie info and directory id
        data = {
            DatabaseEntry.DIRECTORY_KEY.value: directory['_id'],
            DatabaseEntry.METADATA: media_info,
            InternalInfo.RESOLUTION: resolution,
            InternalInfo.CODEC: a_codec,
            DatabaseEntry.CAST: cast  # TODO need to eventually edit this entry to make the cast more easily searchable.
        }

        for key in keyable_info:
            data[key] = movie_info.pop(key)

        data[DatabaseEntry.MISC_INFO] = movie_info

        # Add it to the database, update if already exists
        self.movies.update_one({"_id": tmdb_id}, {"$set": data}, upsert=True)

    def get_movie(self, movie: int | str) -> dict | None:
        if isinstance(movie, str):
            movie = get_tmdb_id(movie)

        return self.movies.find_one({"_id": movie})

    def insert_images(self, mov_id: int, imgs: dict):
        """
        Retrieve a movie from the database using either its TMDB ID or title.

        If an integer is provided, it is treated as a TMDB ID.
        If a string is provided, it is treated as a movie title, and the function will first attempt to translate it into a TMDB ID.

        :param mov_id: The TMDB ID (if an integer) or title (if a string) of the movie to retrieve.
        :param imgs: A dictionary containing the images to be downloaded.
        :return: The movie document from the database, or None if no matching movie was found.
        """

        image_links = {}
        db_entry = {}

        # image download link
        for image_kind, path in imgs.items():
            url = f'https://image.tmdb.org/t/p/original{path}'

            response = requests.get(url)
            if response.status_code == requests.codes.ok:
                # Open the response content as an image using PIL
                image = Image.open(BytesIO(response.content))

                # Save the image to a file
                image_name = Path(self.images_directory / f'{mov_id}_{image_kind}.jpg')
                image.save(image_name)

                image_links[image_kind] = str(image_name)

        db_entry['images'] = image_links

        self.images.update_one({'_id': mov_id}, {"$set": db_entry}, upsert=True)

    def read_config(self, field_name):
        self.config.read(
            'settings.ini')  # TODO change this and the set config version to use the variable and settings.ini.
        try:
            return self.config.get('DEFAULT', field_name)
        except configparser.NoOptionError:
            return None

    def set_config(self, field_name, value):
        self.config.set('DEFAULT', field_name, value)
        with open('settings.ini', 'w') as configfile:
            self.config.write(configfile)

    def set_settings_path(self, path):
        self.settings_path = path

import pathlib
from io import BytesIO
from pathlib import Path
import configparser
import requests
from PIL import Image

from enum import Enum

from pymongo import MongoClient

from InformationGrabbers.file_info import get_res_codec
from InformationGrabbers.get_tmdb_data import get_tmdb_id, make_tmdb_call, compile_cast, get_movie_name
from InformationGrabbers.metadata import get_track_info

from Concurrency.ConcurrentRequests import ConcurrentRequests


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
    PLOT = 'overview'
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


class Cast(str, Enum):
    ADULT = 'adult'
    GENDER = "gender"
    PERSON_ID = "id"
    KNOWN_FOR = "known_for_department"
    NAME_NOW = "name"
    NAME_BEFORE = "original_name"
    POPULARITY = "popularity"
    HEADSHOT = "profile_path"
    CHARACTER_NAME = "character"


keyable_info = (MovieInfo.ADULT, MovieInfo.GENRES)

searchable_info = (MovieInfo.ADULT, MovieInfo.GENRES, InternalInfo.RESOLUTION, InternalInfo.CODEC)


class MovieDatabase:
    def __init__(self, db_url, db_name, async_requester: ConcurrentRequests):
        client = MongoClient(db_url)
        self.db = client[db_name]
        self.movies = self.db['movies']
        self.directories = self.db['directories']
        self.images = self.db['images']
        self.cast = self.db['actors']
        self.seen_before = self.db['movie_ids']

        self.batch_requester = async_requester

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

        if tmdb_id:
            tmdb_id = int(tmdb_id)
        else:
            movie_name = get_movie_name(file_path)
            if movie_name:
                tmdb_id = self.seen_before.find_one({'_id': movie_name})

        if self.movies.find_one({'_id': tmdb_id}) and not force_update:
            # print(f"Skipped the movie {file_path}")
            # TODO probably need to introduce another level, so if its not in the movie file, but we've seen it before, we should create a collection in our mongodb that stores the tmdbids of movies we've seen before.
            return

        # Extract TMDB ID and other metadata from the file
        media_info = get_track_info(file_path)
        if tmdb_id:
            try:
                the_id = int(tmdb_id)
            except ValueError:
                the_id = tmdb_id
            movie_info = make_tmdb_call(the_id)
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

        cast = self.insert_cast(cast)  # mutates cast to be a list of tuples containing the actor id and character name.

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
            data[key] = movie_info.pop(key)  # TODO need to fix genres

        data[DatabaseEntry.MISC_INFO] = movie_info

        # Add it to the database, update if already exists
        self.movies.update_one({"_id": int(tmdb_id)}, {"$set": data}, upsert=True)

    def get_movie(self, movie: int | str) -> dict | None:
        if isinstance(movie, str):
            movie = get_tmdb_id(movie)

        return self.movies.find_one({"_id": int(movie)})

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
                image_name = Path(self.images_directory / 'movies' / f'{mov_id}_{image_kind}.jpg')
                image.save(image_name)

                image_links[image_kind] = str(image_name)

        db_entry['images'] = image_links

        self.images.update_one({'_id': int(mov_id)}, {"$set": db_entry}, upsert=True)

    def get_images(self, movie: int | str) -> dict | None:
        if isinstance(movie, str):
            movie = get_tmdb_id(movie)

        return self.images.find_one({"_id": movie})

    def insert_cast(self, cast: list[dict]) -> list[tuple]:

        cast_member_list = []
        actor_image_dir = Path(self.images_directory / 'actors')
        actor_image_dir.mkdir(exist_ok=True)

        for cast_member in cast:
            url = f'https://image.tmdb.org/t/p/original{cast_member[Cast.HEADSHOT.value]}'

            response = requests.get(url)
            if response.status_code == requests.codes.ok:
                # Open the response content as an image using PIL
                image = Image.open(BytesIO(response.content))

                # Save the image to a file
                image_name = Path(actor_image_dir / f'{cast_member["id"]}.jpg')
                image.save(image_name)

            else:
                image_name = None

            cast_entry = {
                '_id': int(cast_member[Cast.PERSON_ID.value]),
                Cast.ADULT: cast_member[Cast.ADULT.value],
                Cast.GENDER: cast_member[Cast.GENDER.value],
                Cast.KNOWN_FOR: cast_member[Cast.KNOWN_FOR.value],
                Cast.NAME_NOW: cast_member[Cast.NAME_NOW.value],
                Cast.NAME_BEFORE: cast_member[Cast.NAME_BEFORE.value],
                Cast.POPULARITY: cast_member[Cast.POPULARITY.value],
                Cast.HEADSHOT: str(image_name)
            }

            self.cast.update_one({'_id': cast_member['id']}, {'$set': cast_entry}, upsert=True)

            cast_member_list.append((cast_member['id'], cast_member[Cast.CHARACTER_NAME]))

        return cast_member_list

    def get_cast_member(self, cast_id: int) -> dict:
        return self.cast.find_one({"_id": cast_id})

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

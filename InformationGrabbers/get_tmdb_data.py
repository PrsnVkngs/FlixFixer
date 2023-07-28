import pathlib
from pathlib import Path

import requests as r
import json
import re

from InformationGrabbers.get_movie_details_from_file import file_movie_name as mov_name
from InformationGrabbers.get_movie_details_from_file import file_movie_year as mov_year

genre_dictionary = {

    12: "Adventure",
    14: "Fantasy",
    16: "Animation",
    18: "Drama",
    27: "Horror",
    28: "Action",
    35: "Comedy",
    36: "History",
    37: "Western",
    53: "Thriller",
    80: "Crime",
    99: "Documentary",
    878: "Science Fiction",
    9648: "Mystery",
    10402: "Music",
    10749: "Romance",
    10752: "War",
    10751: "Family",
    10770: "TV Movie"

}

tmdbid_pattern = re.compile(r'(?<=\=)[0-9]*')
movie_name_pattern = re.compile(r"(.*?)\(")


def make_tmdb_call(movie_name: str | int) -> dict | None:
    """
    Given a string
    :param movie_name:

    The program will return
    :return:

    A dict type containing the valuable movie information.
    """

    if isinstance(movie_name, str):
        find_id = re.search(tmdbid_pattern, movie_name)

        if find_id:
            mov_id = find_id.group(0)
        else:
            # print("The received movie name was: ", movie_name)

            name = mov_name(movie_name)

            # print("The name gotten back was: ", name)

            year = mov_year(movie_name)

            if name is None:
                return None

            name = name.strip().replace(" ", "%20").replace(".mkv", "").replace(",", "%2C")

            tmdb_call_string = f'https://api.themoviedb.org/3/search/movie?api_key=629b1dbf49450758fdd0904c55158104&' \
                               f'language=en-US&query={name}&page=1&include_adult=false'

            if year:
                tmdb_call_string = tmdb_call_string + f'&year={year}'

            # print("movie info:", name, year)

            tmdb_response = r.get(tmdb_call_string, timeout=6.0)
            movie_info = json.loads(tmdb_response.text)

            if not movie_info["results"]:
                tmdb_call_string = f'https://api.themoviedb.org/3/search/movie?api_key=629b1dbf49450758fdd0904c55158104&' \
                                   f'language=en-US&query={name}&page=1&include_adult=false'
                tmdb_response = r.get(tmdb_call_string, timeout=6.0)
                movie_info = json.loads(tmdb_response.text)

            if not movie_info["results"]:
                return None

            info_list = movie_info["results"][0]

            mov_id = info_list["id"]
    else:
        mov_id = movie_name  # keep in mind that in this case an integer was passed in, presumably the TMDB ID.

    tmdb_id_req = f'https://api.themoviedb.org/3/movie/{mov_id}?api_key=629b1dbf49450758fdd0904c55158104&language=en-US'
    precise_movie = r.get(tmdb_id_req)
    precise_info = json.loads(precise_movie.text)

    # collection = is_part_of_collection(precise_info)
    #
    # info_to_return = {
    #
    #     "id": mov_id,
    #     "collection": None,
    #     "plot": precise_info["overview"],
    #     "genres": compile_genres(precise_info["genres"]),
    #     "tagline": precise_info["tagline"],
    #     "runtime": precise_info["runtime"],
    #     "title": precise_info["title"],
    #     "release_date": precise_info["release_date"],
    #     "ratings": precise_info["vote_average"],
    #     "rt_count": precise_info["vote_count"],
    #     "images": compile_posters(precise_info),
    #     "cast": compile_cast(mov_id)
    #
    # }
    #
    # if collection:
    #     info_to_return.update({"collection": collection})

    return precise_info


def compile_posters(info_list: dict) -> dict[str, str]:
    images = {
        "backdrop_path": info_list["backdrop_path"],
        "poster_path": info_list["poster_path"]
        # "production_companies": info_list["production_companies"]
    }

    if info_list['belongs_to_collection']:
        images['coll_poster_path'] = info_list['belongs_to_collection']['poster_path']
        images['coll_backdrop_path'] = info_list['belongs_to_collection']['backdrop_path']

    return images


def compile_production(info_list: dict) -> list[dict]:
    return info_list['production_companies']


def compile_cast(mov_id: int) -> list[dict]:
    tmdb_id_req = f'https://api.themoviedb.org/3/movie/{mov_id}/credits?api_key=629b1dbf49450758fdd0904c55158104&language=en-US'

    cast = r.get(tmdb_id_req, timeout=6.0)
    cast_json = json.loads(cast.text)

    return cast_json['cast']


def compile_genres(genre_list):
    """
    Pass in the info_list["genre_ids"] and this function will return a list of genres in text form.
    :param genre_list:
    :return:
    """

    # global genre_dictionary

    genres = []

    for genre_dict in genre_list:  # go through the returned values and get the genre string.
        genres.append(genre_dict["name"])

    # for ids in genre_list:
    #     genres.append(genre_dictionary[ids])

    return genres


def is_part_of_collection(movie_json):
    """
    Given a movie id, this function returns a False boolean if it does not belong to any collection,
    and returns a list with the collection id and name if it does.
    :param movie_json:
    :return:
    """

    collection_info = []

    if type(movie_json["belongs_to_collection"]) == type(None):
        return False
    else:
        collection_info.append(movie_json["belongs_to_collection"]["id"])
        collection_info.append(movie_json["belongs_to_collection"]["name"])

        return collection_info


def get_tmdb_id(movie: Path | str) -> int | None:
    if isinstance(movie, Path):
        movie = str(movie.name)

    tmdb_id = re.search(tmdbid_pattern, movie)
    if tmdb_id:
        tmdb_id = tmdb_id.group(0)

    return tmdb_id


def get_movie_name(movie: Path | str) -> str | None:
    if isinstance(movie, Path):
        movie = str(movie.name)

    movie_name = re.search(movie_name_pattern, movie)
    if movie_name:
        movie_name = movie_name.group(0)
        movie_name = movie_name[:-1]

    return movie_name.strip()


if __name__ == '__main__':
    print(get_movie_name(Path("Arkham Asylum  (2022) [tmdbid].mkv")))

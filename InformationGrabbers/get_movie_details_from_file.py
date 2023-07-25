import re

movie_year_pattern = re.compile(r'(?<=\()[0-9]{4}')
tmdbid_pattern = re.compile(r"\[.+?\]")
year_pattern = re.compile(r"\(.+?\)")


def file_movie_name(file_string):
    """
    This function will return the name of the movie contained in the file name given.
    For example, given:
    Your Highness (2011) [tmdbid=38319].mkv
    This function will return:
    Your Highness
    as a string. If no match is found, (meaning there is a file naming convention that doesn't meet expectations)
    there will be a None return and this can be caught in a try-catch method.

    :param file_string:
    :return:
    """

    global year_pattern  # , tmdbid_pattern

    working_string = file_string[:-4]
    # working_string = re.sub(tmdbid_pattern, "", working_string)
    working_string = re.sub(year_pattern, "", working_string)

    return working_string


"""
    if match:
        return match.group()

    global fallback_movie_patt

    match = re.search(fallback_movie_patt, file_string)
    print("Second match: ", match)

    if match:
        return match.group()

    return str(file_string)[-4:]
"""


def file_movie_year(file_string):
    """
    This function will return the year of the movie in the file name. Will return None if there is none found.
    :param file_string:
    :return:
    """

    global movie_year_pattern

    match = re.search(movie_year_pattern, file_string)

    # print("Movie year found was: ", match)  # TODO remove this before release.

    if match:
        return match.group()
    else:
        return None


def has_tmdb_tag(file_string):
    global tmdbid_pattern

    match = re.search(tmdbid_pattern, file_string)

    if match:
        return True
    else:
        return False

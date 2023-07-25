from PyQt6.QtWidgets import QGridLayout

from MovieDatabase import MovieInfo

movie_info_list = (MovieInfo.ADULT, MovieInfo.GENRES, MovieInfo.PRODUCTION_COUNTRY, MovieInfo.PRODUCTION_COMPANY,
                   MovieInfo.COLLECTION, MovieInfo.TMDB_ID, MovieInfo.IMDB_ID, MovieInfo.BUDGET, MovieInfo.HOMEPAGE,
                   MovieInfo.LANGUAGE, MovieInfo.LANGUAGES, MovieInfo.OVERVIEW, MovieInfo.POPULARITY, MovieInfo.RATERS,
                   MovieInfo.RATING, MovieInfo.REVENUE, MovieInfo.RELEASE, MovieInfo.RUNTIME, MovieInfo.STATUS)

filtered_enum = Enum('FilteredEnum', [(key, value) for key, value in MyEnum.__members__.items() if key not in exclude_keys])

# already have tagling, plot, poster, title. we don't really need to have the backdrop yet.
def create_info_scroller_layout(user_preferences: dict):
    scroller_layout = QGridLayout()



from PyQt6.QtWidgets import QGridLayout, QLabel

from MovieDatabase import MovieInfo

movie_info_list = (MovieInfo.ADULT, MovieInfo.GENRES, MovieInfo.PRODUCTION_COUNTRY, MovieInfo.PRODUCTION_COMPANY,
                   MovieInfo.COLLECTION, MovieInfo.TMDB_ID, MovieInfo.IMDB_ID, MovieInfo.BUDGET, MovieInfo.HOMEPAGE,
                   MovieInfo.LANGUAGE, MovieInfo.LANGUAGES, MovieInfo.PLOT, MovieInfo.POPULARITY, MovieInfo.RATERS,
                   MovieInfo.RATING, MovieInfo.REVENUE, MovieInfo.RELEASE, MovieInfo.RUNTIME, MovieInfo.STATUS)

used_values = (MovieInfo.TITLE_CUR, MovieInfo.TAGLINE, MovieInfo.PLOT, MovieInfo.POSTER, MovieInfo.BACKDROP)


# already have tagling, plot, poster, title. we don't really need to have the backdrop yet.
def create_info_scroller_layout(user_preferences: dict):
    scroller_layout = QGridLayout()

    movie_info_widgets = {}

    row = 0
    for movie_info in MovieInfo:
        if movie_info not in used_values and user_preferences[movie_info]:
            # Creating a label and adding it to the grid layout
            label = QLabel(f"{movie_info.name}: Generic Value")
            scroller_layout.addWidget(label, row % 2, int(row / 2))
            row += 1

            # Storing a reference to the QLabel in the dictionary
            movie_info_widgets[movie_info] = label

    return scroller_layout, movie_info_widgets

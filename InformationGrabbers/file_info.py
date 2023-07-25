from pathlib import Path

from pymediainfo import MediaInfo as mI


def get_res_codec(movie_path: Path) -> tuple:
    info = mI.parse(movie_path)

    resolution = info.video_tracks[0].to_data().get('width')
    audio_codec = info.audio_tracks[0].to_data().get('codec_id')

    return resolution, audio_codec


def get_movies_from_directory(directory: Path, depth: int = 0) -> list[Path]:

    movies = []

    for level in range(depth+1):
        results = directory.glob(f"*{'/*' * level}.mkv")
        for mov in results:
            movies.append(mov)

    return movies

from pathlib import Path

from pymediainfo import MediaInfo as mI


mkvpropedit_keys = {'title', 'track_number', 'name', 'language', 'codec_id', 'codec_name', 'pixel_height',
                    'pixel_width', 'display_height', 'display_width', 'channels', 'bit_depth', 'track_type',
                    'chroma_subsample_vertical', 'chroma_subsample_horizontal', 'sampling_frequency'}

translations = {

    'commercial_name': 'codec_name',
    'channel_s': 'channels',
    'sampling_rate': 'sampling_frequency',
    'sampled_height': 'pixel_height',
    'sampled_width': 'pixel_width',
    'height': 'display_height',
    'width': 'display_width'

}


def filter_track(track_data):
    track_type = track_data['track_type']

    match track_type:
        case 'Video':
            if 'chroma_subsampling' in track_data:
                chroma = track_data.pop('chroma_subsampling')
                chroma = chroma.split(':')
                track_data['chroma_subsample_horizontal'] = chroma[1]
                track_data['chroma_subsample_vertical'] = chroma[2]
                track_data.pop('bit_depth')

                try:
                    bit_rate = track_data['other_bit_rate'][0]
                except KeyError:
                    bit_rate = ''

                try:
                    frame_rate = track_data['other_frame_rate'][0]
                except KeyError:
                    frame_rate = ''

                track_data['name'] = f"{track_data['commercial_name']} [{bit_rate}] ({frame_rate})"

        case 'Audio':
            if 'title' in track_data:
                track_data.pop('title')
            try:
                bit_rate = track_data['other_bit_rate'][0]
            except KeyError:
                bit_rate = ''

            try:
                sampl_rate = track_data['other_sampling_rate'][0]
            except KeyError:
                sampl_rate = ''
            track_data['name'] = f"{track_data['commercial_name']} [{bit_rate}] ({sampl_rate})"
            # print(track_data['commercial_name'])
            # if "Atmos" in

    for old_key in set(translations.keys()).intersection(track_data.keys()):
        key_value = track_data.pop(old_key)
        track_data[translations[old_key]] = key_value

    filtered_track = {key.replace('_', '-'): track_data[key] for key in mkvpropedit_keys if key in track_data.keys()}

    return filtered_track


def get_track_info(path_to):
    """
    Given the directory location of a movie, this function will parse the file into MediaInfo and return the
    available video, audio and text track details. :param path: :param movie: :return: A list of data in dict form
    for the movie file. Elements 1-3 are counters to make it more easily known how many of each track there are.
    Video track is element 4, Audio track is element 5, Text track is element 6. There will be a string saying "not
    available" if media info does not find a track for that type.
    """
    mediainfo_dat = mI.parse(path_to.absolute())

    track_data = {'Video': [], 'Audio': [], 'Subtitles': []}

    # print('constructing track info')
    for tracks in mediainfo_dat.tracks:
        track_type = tracks.track_type
        if track_type in track_data:
            trad = filter_track(tracks.to_data())
            track_data[track_type].append(trad)

    for track_type in track_data:
        if not track_data[track_type]:
            track_data[track_type] = 0

    return track_data

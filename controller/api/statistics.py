from json import dumps
from flask import Blueprint, request
from model.database import Import_song

statistics = Blueprint(
    "statistics",
    __name__,
    template_folder="templates/api/statistics",
    url_prefix="/statistics",
)

@statistics.route("/bySong")
def by_song():
    """
    Returns a list of songs and their votes

    params:
        limit: int - The amount of songs to return
        offset: int - The offset to start from
    returns:
        json - A list of songs
    """
    limit: int = request.args.get("limit", default=10, type=int)
    offset: int = request.args.get("offset", default=0, type=int)

    song_list: list[dict[str, str | int]] = Import_song.stats_by_songs(limit, offset)
    output = {
        "recordsTotal": len(song_list),
        "offset": offset,
        "limit": limit,
        "data": [],
    }
    for song in song_list:
        output["data"].append(
            {
                "song_id": song["id"],
                "song_title": song["song"],
                "artist": song["artist"],
                "count": song["count"],
            }
        )
    return dumps(output)

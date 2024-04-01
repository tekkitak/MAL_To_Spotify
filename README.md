## Spotify Playlist Generator for Anime Watchers

This project aims to generate a personalized Spotify playlist for anime watchers based on their watched list on MyAnimeList.net. The generated playlist will include songs from the soundtracks of the anime shows in the user's watched list.

### How does it work?

The project utilizes the MyAnimeList API to fetch the list of anime shows that the user has watched. It then uses this data to search for the corresponding soundtracks on Spotify through the Spotify Web API. The tracks are then added to a playlist, which is created and shared with the user's Spotify account.

### Requirements

- A Spotify developer account to access the Spotify Web API
- MyAnimeList account with API key
- SQLite
- Python 3.x

### Installation

To setup the application

```
git clone https://github.com/tekkitak/MAL_To_Spotify
python -m venv venv
source venv/bin/activate
pip install -r requirements
```

You will need to get MyAnimeList API key, which you can get [here](https://myanimelist.net/apiconfig/create).

You will also need to set up a Spotify developer account and create an application to obtain your API credentials. You can find more information on how to do this in the [Spotify Web API Documentation](https://developer.spotify.com/documentation/web-api/).

### Usage

1. copy example.env into .env (`cp example.env .env`)
2. Replace all the necceseary values in your .env with editor of choice
3. Execute `flask db-init` to initiate the database
4. Run `flask run` in your terminal to start the Flask application.
5. Open your web browser and navigate to `http://localhost:5000`.

### Further information

If you have any further questions or suggestions for improving this project, please feel free to contact the project maintainer or open an issue on the GitHub repository.

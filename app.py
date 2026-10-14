from flask import Flask, request, redirect, Response, render_template
from flask.typing import ResponseReturnValue
from data_manager import DataManager
from models import db, Movie
from dotenv import load_dotenv
import requests
import os

load_dotenv()


app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'data/movies.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)  # Link the database and the app. This is the reason you need to import db from models

data_manager = DataManager() # Create an object of your DataManager class


@app.route('/', methods=['GET'])
def home() -> str:
    users = data_manager.get_users()
    return render_template(
        "index.html",
        users=users
    )


@app.route('/users', methods=['POST'])
def create_user() -> Response:
    user_name = request.form["user_name"]
    data_manager.create_user(user_name)
    return redirect("/")


@app.route('/users/<int:user_id>/movies', methods=['GET'])
def get_user_favorite_movies(user_id: int) -> str:
    favorite_movies = data_manager.get_movies(user_id)

    return render_template(
        "movies.html",
        movies=favorite_movies,
        user_id=user_id
    )


@app.route("/users/<int:user_id>/movies/search", methods=["POST"])
def find_movies(user_id: int) -> ResponseReturnValue:
    query_title = request.form["movie"]
    api_key = os.getenv("OMDB_API_KEY")

    response = requests.get(
        "https://www.omdbapi.com/",
        params={
            "apikey": api_key,
            "s": query_title,
            "type": "movie"
        },
        timeout=10
    )

    response.raise_for_status()
    data = response.json()

    if data.get("Response") == "False":
        return render_template(
            "error.html",
            message=data.get("Error", "No movies found.")
        ), 404

    return render_template(
        "movie_search_results.html",
        movies=data["Search"],
        user_id=user_id
    )


@app.route("/users/<int:user_id>/movies", methods=["POST"])
def add_user_favorite_movie(user_id: int) -> ResponseReturnValue:
    imdb_id = request.form["final_imdb_id"]
    api_key = os.getenv("OMDB_API_KEY")

    response = requests.get(
        "https://www.omdbapi.com/",
        params={
            "apikey": api_key,
            "i": imdb_id
        },
        timeout=10
    )

    response.raise_for_status()
    movie = response.json()

    if movie.get("Response") == "False":
        return render_template(
            "error.html",
            message=movie.get("Error", "Movie could not be loaded.")
        ), 404

    new_movie = Movie(
        title=movie["Title"],
        year=int(movie["Year"]),
        director=movie["Director"],
        poster_url=movie["Poster"]
    )

    data_manager.add_movie(user_id, new_movie)

    return redirect(f"/users/{user_id}/movies")


@app.route('/users/<int:user_id>/movies/<int:movie_id>/update', methods=['POST'])
def update_personal_movie_title(user_id: int, movie_id: int) -> Response:
    custom_title = request.form["custom_title"]
    data_manager.update_movie(user_id, movie_id, custom_title)

    return redirect(f"/users/{user_id}/movies")


@app.route('/users/<int:user_id>/movies/<int:movie_id>/delete', methods=['POST'])
def delete_personal_movie(user_id: int, movie_id: int) -> Response:
    data_manager.delete_movie(user_id, movie_id)

    return redirect(f"/users/{user_id}/movies")


@app.errorhandler(404)
def page_not_found(_error) -> ResponseReturnValue:
    return render_template(
        "404.html"
    ), 404


@app.errorhandler(500)
def internal_server_error(_error) -> ResponseReturnValue:
    return render_template(
        "error.html",
        message="Something went wrong on the server."
    ), 500


@app.errorhandler(requests.RequestException)
def handle_omdb_request_error(
    error: requests.RequestException
) -> ResponseReturnValue:
    print(f"OMDb request failed: {error}")

    return render_template(
        "error.html",
        message="The movie service is currently unavailable."
    ), 502


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run()
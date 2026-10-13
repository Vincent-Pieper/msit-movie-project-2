from flask import Flask, request, redirect, Response, render_template
import requests
from data_manager import DataManager
from models import db, Movie
from dotenv import load_dotenv
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
    print(users)
    return "Home"


@app.route('/users', methods=['POST'])
def create_user() -> Response:
    user_name = request.form["user_name"]
    data_manager.create_user(user_name)
    return redirect("/")


@app.route('/users/<int:user_id>/movies', methods=['GET'])
def get_user_favorite_movies(user_id: int) -> Response:
    favorite_movies = data_manager.get_movies(user_id)
    for movie in favorite_movies:

        print(movie) # !! custom name must override original title !!
    return "Movies loaded."


@app.route('/users/<int:user_id>/movies/search', methods=['POST'])
def find_movies(user_id: int):
    query_title = request.form["movie"]
    api_key = os.getenv("OMDB_API_KEY")

    response = requests.get(
        "https://www.omdbapi.com/",
        params={
            "apikey": api_key,
            "s": query_title,
            "type": "movie"
        }
    )

    data = response.json()

    if data.get("Response") == "False":
        print(data.get("Error"))
        return "No movies found."

    return render_template(
        "movie_search_results.html",
        movies=data["Search"],
        user_id=user_id
    )


@app.route('/users/<int:user_id>/movies', methods=['POST'])
def add_user_favorite_movie(user_id: int) -> Response:
    query_title = request.form["final_movie"]
    query_year = request.form["final_year"]
    api_key = os.getenv("OMDB_API_KEY")

    response = requests.get(
        "https://www.omdbapi.com/",
        params={
            "apikey": api_key,
            "t": query_title,
            "y": query_year,
            "type": "movie"
        }
    )

    movie = response.json()
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


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

  app.run()
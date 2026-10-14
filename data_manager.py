from models import db, User, Movie, UserFavorite
from sqlalchemy import select

class DataManager:
    def create_user(self, name):
        new_user = User(name=name)

        with db.session.begin():
            db.session.add(new_user)

    def get_users(self):
        stmt = select(User).order_by(User.name)
        return db.session.scalars(stmt).all()

    def get_movies(self, user_id) -> list[Movie]:
        stmt = (
            select(Movie, UserFavorite.custom_title)
            .join(UserFavorite, Movie.id == UserFavorite.movie_id)
            .where(UserFavorite.user_id == user_id)
        )
        return db.session.execute(stmt).all()

    def add_movie(self, user_id: int, movie: Movie) -> None:
        with db.session.begin():
            existing_movie = self.get_movie(movie.title, movie.year)
            if not existing_movie:
                self._flush_movie(movie)
                existing_movie = movie
            movie_id = existing_movie.id
            favorite_exists = self._get_favorite_movie(user_id, movie_id)
            if not favorite_exists:
                self._add_favorite_movie(user_id, movie_id)

    def get_movie(self, title: str, year: int) -> Movie | None:
        stmt = select(Movie).where(Movie.title == title).where(Movie.year == year)
        movie = db.session.scalars(stmt).one_or_none()
        return movie

    def _flush_movie(self, movie: Movie) -> None:
        db.session.add(movie)
        db.session.flush()

    def _add_favorite_movie(self, user_id: int, movie_id: int) -> None:
        new_favorite = UserFavorite(
            user_id=user_id,
            movie_id=movie_id
        )
        db.session.add(new_favorite)

    def _get_favorite_movie(self, user_id: int, movie_id: int) -> UserFavorite | None:
        stmt = select(UserFavorite).where(UserFavorite.user_id == user_id).where(UserFavorite.movie_id == movie_id)
        return db.session.scalars(stmt).one_or_none()

    def update_movie(self, user_id: int, movie_id: int, new_title: str) -> None:
        with db.session.begin():
            custom_movie = self._get_favorite_movie(user_id, movie_id)
            if not custom_movie:
                return
            custom_movie.custom_title = new_title

    def delete_movie(self, user_id: int, movie_id: int) -> None:
        with db.session.begin():
            delete_movie = self._get_favorite_movie(user_id, movie_id)
            if not delete_movie:
                return
            db.session.delete(delete_movie)

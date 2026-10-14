from models import db, User, Movie, UserFavorite
from sqlalchemy import select

class DataManager:
    """Manage database operations for the MoviWeb application."""

    def create_user(self, name):
        """Create a new user."""
        new_user = User(name=name)

        with db.session.begin():
            db.session.add(new_user)

    def get_users(self):
        """Return all users ordered by name."""
        stmt = (
            select(User)
            .order_by(User.name)
        )
        return db.session.scalars(stmt).all()

    def get_movies(self, user_id):
        """Return all favorite movies and custom titles for a user."""
        stmt = (
            select(Movie, UserFavorite.custom_title)
            .join(UserFavorite, Movie.id == UserFavorite.movie_id)
            .where(UserFavorite.user_id == user_id)
        )
        return db.session.execute(stmt).all()

    def add_movie(self, user_id: int, movie: Movie) -> bool:
        """Add a movie to a user's favorites if it is not already present."""
        with db.session.begin():
            existing_movie = self.get_movie(movie.title, movie.year)

            if not existing_movie:
                self._flush_movie(movie)
                existing_movie = movie

            movie_id = existing_movie.id
            favorite_exists = self._get_favorite_movie(user_id, movie_id)

            if favorite_exists:
                return False

            self._add_favorite_movie(user_id, movie_id)
            return True

    def get_movie(self, title: str, year: int) -> Movie | None:
        """Return a movie matching the given title and year."""
        stmt = (
            select(Movie)
            .where(Movie.title == title)
            .where(Movie.year == year)
        )
        movie = db.session.scalars(stmt).one_or_none()
        return movie

    def _flush_movie(self, movie: Movie) -> None:
        """Add a movie and flush the session to generate its database ID."""
        db.session.add(movie)
        db.session.flush()

    def _add_favorite_movie(self, user_id: int, movie_id: int) -> None:
        """Create a favorite relationship between a user and a movie."""
        new_favorite = UserFavorite(
            user_id=user_id,
            movie_id=movie_id
        )
        db.session.add(new_favorite)

    def _get_favorite_movie(
            self,
            user_id: int,
            movie_id: int
    ) -> UserFavorite | None:
        """Return a favorite relationship for the given user and movie."""
        stmt = (
            select(UserFavorite)
            .where(UserFavorite.user_id == user_id)
            .where(UserFavorite.movie_id == movie_id)
        )
        return db.session.scalars(stmt).one_or_none()

    def update_movie(
            self,
            user_id: int,
            movie_id: int,
            new_title: str
    ) -> bool:
        """Update the user-specific title of a favorite movie."""
        with db.session.begin():
            custom_movie = self._get_favorite_movie(user_id, movie_id)

            if not custom_movie:
                return False

            custom_movie.custom_title = new_title
            return True

    def delete_movie(self, user_id: int, movie_id: int) -> bool:
        """Remove a movie from a user's favorites."""
        with db.session.begin():
            favorite = self._get_favorite_movie(user_id, movie_id)

            if not favorite:
                return False

            db.session.delete(favorite)
            return True

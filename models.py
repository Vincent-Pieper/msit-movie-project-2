from __future__ import annotations
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship


db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    user_favorites: Mapped[list["UserFavorite"]] = relationship(back_populates="user")


class Movie(db.Model):
    __tablename__ = "movies"

    __table_args__ = (
        UniqueConstraint("title", "year", name="uq_movie_title_year"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    director: Mapped[str | None] = mapped_column(String, nullable=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    poster_url: Mapped[str | None] = mapped_column(String, nullable=True)

    user_favorites: Mapped[list[UserFavorite]] = relationship(back_populates="movie")


class UserFavorite(db.Model):
    __tablename__ = "user_favorites"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), primary_key=True)
    custom_title: Mapped[str | None] = mapped_column(String, nullable=True)

    user: Mapped[User] = relationship(back_populates="user_favorites")
    movie: Mapped[Movie] = relationship(back_populates="user_favorites")
import wtforms
from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from sqlalchemy import desc
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired
import requests
MOVIES_API_KEY = "insert your api key here"
db = SQLAlchemy()
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# initialize the app with the extension
db.init_app(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(300), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    review = db.Column(db.String(160), nullable=False)
    img_url = db.Column(db.String(300), default="https://c.neevacdn.net/image/fetch/s--z9zdmjz3--/https%3A//mir-s3-cdn-cf.behance.net/project_modules/disp/9556d16312333.5691dd2255721.jpg?savepath=9556d16312333.5691dd2255721.jpg" ,nullable=False)


class AddMovieForm(FlaskForm):
    title = StringField('title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')


class UpdateMovieForm(FlaskForm):
    rating = FloatField('rating', validators=[DataRequired()])
    review = StringField('review', validators=[DataRequired()])
    submit = SubmitField('Update')


with app.app_context():
    db.create_all()


# with app.app_context():
#     db.session.add(new_movie)
#     db.session.commit()


@app.route("/")
def home():
    with app.app_context():
        all_movies = db.session.query(Movie).order_by(desc(Movie.rating)).all()
    return render_template("index.html", movies=enumerate(all_movies), no_movies=not all_movies)


@app.route("/add", methods=["GET", "POST"])
def add():
    form = AddMovieForm()
    if form.validate_on_submit():
        return redirect(url_for('select', movie_title=form.title.data))
    return render_template('add.html', form=form)


@app.route("/add/select/<movie_title>")
def select(movie_title):

    movies_url = f"https://api.themoviedb.org/3/search/movie?api_key={MOVIES_API_KEY}&query={movie_title}" \
                 "&include_adult=true"
    movies_res = requests.get(movies_url)
    movies_res.raise_for_status()
    return render_template("select.html", options=movies_res.json()["results"])


@app.route("/db/<movie_id>")
def add_to_database(movie_id):
    movie_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={MOVIES_API_KEY}&language=en-US"
    movie_res = requests.get(movie_url)
    movie_data = movie_res.json()
    release_date = movie_data['release_date']
    release_date = release_date.split('-')
    movie_year = release_date[0]
    with app.app_context():
        new_movie = Movie(title=movie_data['original_title'], year=movie_year,
                          description=movie_data['overview'],
                          rating=movie_data['vote_average'], review="Best Movie",
                          img_url=f"https://image.tmdb.org/t/p/original{movie_data['poster_path']}")
        db.session.add(new_movie)
        db.session.commit()
    return redirect(url_for('edit', id=Movie.query.filter_by(title=movie_data['original_title']).one().id))


@app.route("/edit/<id>", methods=["GET", "POST"])
def edit(id):
    form = UpdateMovieForm()
    with app.app_context():
        movie_to_update = Movie.query.get(id)
        if form.validate_on_submit():
            movie_to_update.rating = form.rating.data
            movie_to_update.review = form.review.data
            db.session.commit()
            return redirect(url_for('home'))
    return render_template('edit.html', form=form, movie=movie_to_update)


@app.route("/delete/<id>")
def delete(id):
    with app.app_context():
        movie_to_delete = Movie.query.get(id)
        db.session.delete(movie_to_delete)
        db.session.commit()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)

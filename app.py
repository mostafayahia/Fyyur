#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from datetime import datetime
import re
import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO==: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Show(db.Model):
  __tablename__ = 'shows'

  venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), primary_key=True)
  artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), primary_key=True)
  start_time = db.Column(db.DateTime, primary_key=True)

  def __repr__(self):
    return f'<Show venue_id: {self.venue_id}, artist_id: {self.artist_id}, start_time: {self.start_time}>'

class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.String(120), nullable=False)
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(700))
    artists = db.relationship('Artist', secondary='shows', backref=db.backref('venues', lazy=True))

    def __repr__(self):
      return f'<Venue id: {self.id}, name: {self.name}>'

    # TODO==: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(700))

    def __repr__(self):
      return f'<Artist id: {self.id}, name: {self.name}>'
  
  
    # TODO==: implement any missing fields, as a database migration using Flask-Migrate

# TODO== Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO==: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.

  # getting all the venues
  venues = Venue.query.all()

  # grouping the venues by city and state
  city_state_dic = {}
  for v in venues:
    city_state = v.city.lower() + ', ' + v.state.lower()
    vlist = city_state_dic.get(city_state)
    if not vlist:
      vlist = []
      city_state_dic[city_state] = vlist
    vlist.append(v)

  # construct final dic to send as a model to the view
  data = []
  for value in city_state_dic.values():
    data.append({
      'city': value[0].city,
      'state': value[0].state,
      'venues': value
    })
  
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO==: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term = request.form.get('search_term', '')
  like_search = '%{}%'.format(search_term)
  data = Venue.query.filter(Venue.name.ilike(like_search)).all()

  response={
    "count": len(data),
    "data": data
  }

  return render_template('pages/search_venues.html', results=response, search_term = search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO##: replace with real venue data from the venues table, using venue_id
  
  # using sqlalchemy to get the data from db
  venue = Venue.query.get(venue_id)
  
  if not venue:
    return abort(404)

  artists_dic = {}
  def get_show_data(show):
    artist_id_str = str(show.artist_id)
    if not artists_dic.get(artist_id_str):
      artists_dic[artist_id_str] = Artist.query.get(show.artist_id)
    artist = artists_dic[artist_id_str]
    return {
      'start_time': show.start_time.isoformat(),
      'artist_id': artist.id,
      'artist_name': artist.name,
      'artist_image_link': artist.image_link
    }
  
  past_shows = []
  for show in Show.query.filter(Show.start_time < datetime.now(), Show.venue_id == venue_id).all():
    past_shows.append(get_show_data(show))
    
  upcoming_shows = []
  for show in Show.query.filter(Show.start_time > datetime.now(), Show.venue_id == venue_id).all():
    upcoming_shows.append(get_show_data(show))

  # construct the final data dictionary to send to the view page
  data = vars(venue).copy()
  data.pop('_sa_instance_state', None)
  data['upcoming_shows'] = upcoming_shows
  data['past_shows'] = past_shows
  data['genres'] = re.compile(',\s*').split(data['genres']) # split by comma
  data['past_shows_count'] = len(past_shows)
  data['upcoming_shows_count'] = len(upcoming_shows)

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO==: insert form data as a new Venue record in the db, instead
  # TODO==: modify data to be the data object returned from db insertion

  try:
    error = False
    venue = Venue(name=request.form.get('name'), city=request.form.get('city'),
      state=request.form.get('state'), address=request.form.get('address'),
      genres=', '.join(request.form.getlist('genres')), phone=request.form.get('phone'), 
      facebook_link=request.form.get('facebook_link'))
    db.session.add(venue)
    flash_message = f'Venue {venue.name} was successfully listed'
    db.session.commit()
  except:
    error = True
    flash_message = f"An error occurred. Venue {request.form.get('name', '')} could not be listed"
    print(sys.exc_info())
    db.session.rollback()
  finally:
    db.session.close()

  # on successful db insert, flash success
  #flash('Venue ' + request.form['name'] + ' was successfully listed!')
  # TODO==: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  flash(flash_message, 'error') if error else flash(flash_message)

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO==: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    body = {'state': 'success'}
    db.session.commit()
  except:
    error = True
    body = {'state': 'failed'}
    print(sys.exc_info())
    db.session.rollback()
  finally:
    db.session.close()
  return jsonify(body)
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO==: replace with real data returned from querying the database
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO==: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term = request.form.get('search_term', '')
  like_search = '%{}%'.format(search_term)
  artists = Artist.query.filter(Artist.name.ilike(like_search)).all()
  response = {
    "count": len(artists),
    "data": artists
  }
  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO==: replace with real venue data from the venues table, using venue_id
  
  # using sqlalchemy to get the data from db
  artist = Artist.query.get(artist_id)

  if not artist:
    abort(404)
  
  venues_dic = {}
  def get_show_data(show):
    venue_id_str = str(show.venue_id)
    if not venues_dic.get(venue_id_str):
      venues_dic[venue_id_str] = Venue.query.get(show.venue_id)
    venue = venues_dic[venue_id_str]
    return {
      'start_time': show.start_time.isoformat(),
      'venue_id': venue.id,
      'venue_name': venue.name,
      'venue_image_link': venue.image_link
    }
  
  past_shows = []
  for show in Show.query.filter(Show.start_time < datetime.now(), Show.artist_id == artist_id).all():
    past_shows.append(get_show_data(show))
    
  upcoming_shows = []
  for show in Show.query.filter(Show.start_time > datetime.now(), Show.artist_id == artist_id).all():
    upcoming_shows.append(get_show_data(show))

  # construct the final data dictionary to send to the view page
  data = vars(artist).copy()
  data.pop('_sa_instance_state', None)
  data['upcoming_shows'] = upcoming_shows
  data['past_shows'] = past_shows
  data['genres'] = re.compile(',\s*').split(data['genres']) # split by comma
  data['past_shows_count'] = len(past_shows)
  data['upcoming_shows_count'] = len(upcoming_shows)

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)

  if not artist:
    abort(404)
  
  # set default values for genres
  form.genres.default = re.compile(',\s*').split(artist.genres)
  form.process()

  # TODO==: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO==: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  artist = Artist.query.get(artist_id)
  if not artist:
    abort(404)
  artist_name = artist.name

  try:
    artist.name = request.form.get('name')
    artist.city = request.form.get('city')
    artist.state = request.form.get('state')
    artist.phone = request.form.get('phone')
    artist.genres = ', '.join(request.form.getlist('genres'))
    artist.facebook_link = request.form.get('facebook_link')
    db.session.commit()
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash(f'An error occured. could not update artist {artist_name}', 'error')
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  if not venue:
    abort(404)
  # setting default values for genres
  form.genres.default = re.compile(',\s*').split(venue.genres)
  form.process()
  # TODO==: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO==: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  venue = Venue.query.get(venue_id)
  if not venue:
    abort(404)
  venue_name = venue.name

  try:
    venue.name = request.form.get('name')
    venue.city = request.form.get('city')
    venue.state = request.form.get('state')
    venue.address = request.form.get('address')
    venue.phone = request.form.get('phone')
    venue.genres = ', '.join(request.form.getlist('genres'))
    venue.facebook_link = request.form.get('facebook_link')
    db.session.commit()
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash(f'An error occured. could not update venue {venue_name}', 'error')
  finally:
    db.session.close()

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO==: insert form data as a new Venue record in the db, instead
  # TODO==: modify data to be the data object returned from db insertion
  try:
    error = False
    artist = Artist(name=request.form.get('name'), city=request.form.get('city'),
      state=request.form.get('state'), genres=', '.join(request.form.getlist('genres'))
      ,phone=request.form.get('phone'), facebook_link=request.form.get('facebook_link')
      )
    db.session.add(artist)
    flash_message = f'Artist {artist.name} was successfully listed'
    db.session.commit()
  except:
    error = True
    flash_message = f"An error occurred. Artist {request.form.get('name', '')} could not be listed"
    print(sys.exc_info())
    db.session.rollback()
  finally:
    db.session.close()

  # on successful db insert, flash success
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  flash(flash_message, 'error') if error else flash(flash_message) 

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.

  venues_dic = {}
  artists_dic = {}
  def get_show_data(show):
    venue_id_str = str(show.venue_id)
    artist_id_str = str(show.artist_id)
    if not venues_dic.get(venue_id_str):
      venues_dic[venue_id_str] = Venue.query.get(show.venue_id)
    if not artists_dic.get(artist_id_str):
      artists_dic[artist_id_str] = Artist.query.get(show.artist_id)
    artist = artists_dic[artist_id_str]
    venue = venues_dic[venue_id_str]
    return {
      'start_time': show.start_time.isoformat(),
      'venue_id': venue.id,
      'venue_name': venue.name,
      'venue_image_link': venue.image_link,
      'artist_id': artist.id,
      'artist_name': artist.name,
      'artist_image_link': artist.image_link
    }
  
  data = []
  for show in Show.query.all():
    data.append(get_show_data(show))
  
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO==: insert form data as a new Show record in the db, instead
  try:
    error = False
    show = Show(artist_id=request.form.get('artist_id'), 
      venue_id=request.form.get('venue_id'),
      start_time=request.form.get('start_time')
    )
    db.session.add(show)
    flash_message = 'Show was successfully listed!'
    db.session.commit()
  except:
    error = True
    flash_message = 'An error occurred. Show could not be listed'
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()

  # on successful db insert, flash success
  # TODO==: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  flash(flash_message, 'error') if error else flash(flash_message)

  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''

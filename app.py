import os

from flask import Flask, render_template, request, flash, redirect, session, g, url_for
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from forms import UserAddForm, LoginForm, MessageForm, UserEditForm
from models import db, connect_db, User, Message, Follows, Likes

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
# app.config['SQLALCHEMY_DATABASE_URI'] = (
#     os.environ.get('DATABASE_URL', 'postgresql:///warbler'))
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql://postgres:17273185@localhost/warbler'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
toolbar = DebugToolbarExtension(app)

connect_db(app)


##############################################################################
# User signup/login/logout


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect(url_for('homepage'))

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect(url_for('homepage'))

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""

    # IMPLEMENT THIS
    flash("You have been logout.", 'primary')
    do_logout()
    return redirect(url_for('login'))


##############################################################################
# General user routes:

@app.route('/users')
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """

    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', users=users)

# On a profile page, it should show how many warblers that user has 
# liked, and this should link to a page showing their liked warbles.
@app.route('/users/<int:user_id>')
def users_show(user_id):
    """Show user profile."""

    user = User.query.get_or_404(user_id)

    # snagging messages in order from the database;
    # user.messages won't be in order by default
    messages = (Message
                .query
                .filter(Message.user_id == user_id)
                .order_by(Message.timestamp.desc())
                .limit(100)
                .all())
    return render_template('users/show.html', user=user, messages=messages)


@app.route('/users/<int:user_id>/likes')
def users_likes(user_id):

    user = User.query.get_or_404(user_id)

    if g.user:

        messages = (Message
                    .query
                    .join(Likes, Message.id == Likes.message_id)
                    .filter(Likes.user_id == g.user.id)
                    .order_by(Message.timestamp.desc())
                    .limit(100)
                    .all())

        likes = [msg.id for msg in g.user.likes]

        return render_template('users/likes.html', user=user, messages=messages, likes=likes)


@app.route('/users/<int:user_id>/following')
def show_following(user_id):
    """Show list of people this user is following."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect(url_for('homepage'))

    user = User.query.get_or_404(user_id)
    return render_template('users/following.html', user=user)


@app.route('/users/<int:user_id>/followers')
def users_followers(user_id):
    """Show list of followers of this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect(url_for('homepage'))

    user = User.query.get_or_404(user_id)
    return render_template('users/followers.html', user=user)


@app.route('/users/follow/<int:follow_id>', methods=['POST'])
def add_follow(follow_id):
    """Add a follow for the currently-logged-in user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect(url_for('homepage'))

    followed_user = User.query.get_or_404(follow_id)
    g.user.following.append(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route('/users/stop-following/<int:follow_id>', methods=['POST'])
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect(url_for('homepage'))

    followed_user = User.query.get(follow_id)
    g.user.following.remove(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route('/users/profile', methods=["GET", "POST"])
def profile():
    """Update profile for current user."""

    # IMPLEMENT THIS

    # user authentication
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect(url_for('homepage'))
    
    # pre-populate the form with current user's data
    form = UserEditForm(obj=g.user)

    if form.validate_on_submit():
        # check if the password provided by user is valid
        password = form.password.data
        user = User.authenticate(g.user.username, password)

        if user:
            # update the user's details based on the form input
            g.user.username = form.username.data
            g.user.email = form.email.data
            g.user.image_url = form.image_url.data
            g.user.header_image_url = form.header_image_url.data
            g.user.bio = form.bio.data
            # commit the changes to the databse
            db.session.commit()
            flash("Profile updated successfully!", "success")
            return redirect(url_for('users_show', user_id=g.user.id))
        else:
            flash("invalid password", "danger")
            return redirect(url_for('homepage'))

    return render_template("users/edit.html", form=form)


@app.route('/users/delete', methods=["POST"])
def delete_user():
    """Delete user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect(url_for('homepage'))

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect("/signup")


##############################################################################
# Messages routes:

@app.route('/messages/new', methods=["GET", "POST"])
def messages_add():
    """Add a message:

    Show form if GET. If valid, update message and redirect to user page.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect(url_for('homepage'))

    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(text=form.text.data)
        g.user.messages.append(msg)
        db.session.commit()

        return redirect(f"/users/{g.user.id}")

    return render_template('messages/new.html', form=form)


@app.route('/messages/<int:message_id>', methods=["GET"])
def messages_show(message_id):
    """Show a message."""

    msg = Message.query.get(message_id)
    return render_template('messages/show.html', message=msg)


@app.route('/messages/<int:message_id>/delete', methods=["POST"])
def messages_destroy(message_id):
    """Delete a message."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect(url_for('homepage'))

    msg = Message.query.get(message_id)
    db.session.delete(msg)
    db.session.commit()

    return redirect(f"/users/{g.user.id}")


##############################################################################
# Homepage and error pages


@app.route('/')
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of followed_users
    """

    if g.user:
        # Using conditional inner join
        # Show the last 100 messages only from:
        #   1. the users that the logged-in user is following
        #   2. and the logged-in user
        # `follows` and `messages` tables have no relationship set up

        messages = (Message
                    .query
                    .join(Follows, Message.user_id == Follows.user_being_followed_id)
                    .filter((Message.user_id==g.user.id) | (Follows.user_following_id==g.user.id))
                    .order_by(Message.timestamp.desc())
                    .limit(100)
                    .all())

        likes = [msg.id for msg in g.user.likes]

        return render_template('home.html', messages=messages, likes=likes)

    else:
        return render_template('home-anon.html')


# When a user tries to access a resource (such as a webpage) that doesn't exist on the server.
# 404 means "Not Found"
# Create a 404 error handler with `@app.errorhandler` decorator
# This decorator tells Flask to handle 404 errors with `page_not_found` function
@app.errorhandler(404)
def page_not_found(e):
    """ custom 404 error page """

    # `, 404`: sets the status code of the HTTP response to 404
    # without `, 404`, Flask would return a `200 OK` response along with `404.html`
    return render_template('404.html', error=e), 404

##############################################################################
# Turn off all caching in Flask
#   (useful for dev; in production, this kind of stuff is typically
#   handled elsewhere)
#
# https://stackoverflow.com/questions/34066804/disabling-caching-in-flask

@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req


#############################################################################
# LIKES ROUTE

@app.route('/users/add_like/<int:msg_id>', methods=["POST"])
def toggle_like(msg_id):
    """ Allow a user to like a warble written by other users """

    # Check if the user is logged in
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect(url_for('homepage'))

    message = Message.query.get_or_404(msg_id)

    # Ensure the logged-in user cannot like their own warble
    if message.user_id == g.user.id:
        flash("You cannot like your own warble.", "danger")
        return redirect(url_for('homepage'))
    
    # Update liked messsage 
    if message in g.user.likes:
        g.user.likes.remove(message)
    else: 
        g.user.likes.append(message)

    # Update database
    db.session.commit()

    return redirect(url_for('homepage'))

    # NOT ABLE TO TOGGLE A LIKED MESSAGE
    # 
    # 1ST ATTEMPT: Passed the `likes` variable to `url_for` 
    # Extraced a list of id from the `g.user.likes` and assigned the value to `likes`
    # This resulted a multiple query string in the url as follow:
    # http://127.0.0.1:5000/?likes=222&likes=767&likes=784
    # 
    # 2ND ATTEMPT: Inspecting `homepage` route
    # `likes` was not defined and passed to the template




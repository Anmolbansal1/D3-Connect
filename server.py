import os

from jinja2 import StrictUndefined

from flask import Flask, render_template, redirect, request, flash, session, jsonify
from flask_debugtoolbar import DebugToolbarExtension

from model import User, Connection
from model import connect_to_db, db
from friends import is_friends_or_pending, get_friend_requests, get_friends
from preds import age_sim, occ_sim, location_sim, interest_sim

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy_searchable import search

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET_KEY", "abcdef")
app.jinja_env.undefined = StrictUndefined

from raven.contrib.flask import Sentry
sentry = Sentry(app)

from  geopy.geocoders import Nominatim
from math import radians, degrees, sin, cos, asin, acos, sqrt 
geolocator = Nominatim()

@app.route('/')
def index():
    """Homepage."""

    return render_template("homepage.html")


@app.route("/login", methods=["GET"])
def show_login():
    """Show login form."""

    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    """Log user in if credentials provided are correct."""

    login_email = request.form.get("login_email")
    login_password = request.form.get("login_password")

    try:
        current_user = db.session.query(User).filter(User.email == login_email,
                                                     User.password == login_password).one()
    except NoResultFound:
        flash("The email or password you have entered did not match our records. Please try again.", "danger")
        return redirect("/login")

    # Get current user's friend requests and number of requests to display in badges
    received_friend_requests, sent_friend_requests = get_friend_requests(current_user.user_id)
    num_received_requests = len(received_friend_requests)
    num_sent_requests = len(sent_friend_requests)
    num_total_requests = num_received_requests + num_sent_requests

    # Use a nested dictionary for session["current_user"] to store more than just user_id
    session["current_user"] = {
        "first_name": current_user.first_name,
        "user_id": current_user.user_id,
        "num_received_requests": num_received_requests,
        "num_sent_requests": num_sent_requests,
        "num_total_requests": num_total_requests
    }

    flash("Welcome {}. You have successfully logged in.".format(current_user.first_name), "success")

    return redirect("/users/{}".format(current_user.user_id))


@app.route("/logout")
def logout():
    """Log user out."""

    del session["current_user"]

    flash("Goodbye! You have successfully logged out.", "success")

    return redirect("/")


@app.route("/signup", methods=["GET"])
def show_signup():
    """Show signup form."""

    return render_template("signup.html")


@app.route("/signup", methods=["POST"])
def signup():
    """Check if user exists in database, otherwise add user to database."""

    signup_email = request.form.get("signup_email")
    signup_password = request.form.get("signup_password")
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")


    try:
        db.session.query(User).filter(User.email == signup_email).one()

    except NoResultFound:
        new_user = User(
                        email=signup_email,
                        password=signup_password,
                        first_name=first_name,
                        last_name=last_name)
        db.session.add(new_user)
        db.session.commit()

        # Add same info to session for new user as per /login route
        session["current_user"] = {
            "first_name": new_user.first_name,
            "user_id": new_user.user_id,
            "num_received_requests": 0,
            "num_sent_requests": 0,
            "num_total_requests": 0
        }

        flash("You have succesfully signed up for an account, and you are now logged in.", "success")

        return redirect("/users/%s" % new_user.user_id)

    flash("An account already exists with this email address. Please login.", "danger")

    return redirect("/login")


@app.route("/users")
def user_list():
    """Show list of users."""

    users = db.session.query(User).all()

    return render_template("user_list.html",
                           users=users)


@app.route("/users/<int:user_id>")
def user_profile(user_id):
    """Show user profile with map and list of visited restaurants."""

    user = db.session.query(User).filter(User.user_id == user_id).one()

    total_friends = len(get_friends(user.user_id).all())

    user_a_id = session["current_user"]["user_id"]
    user_b_id = user.user_id

    extra_completed = user.age and user.gender

    # Check connection status between user_a and user_b
    friends, pending_request = is_friends_or_pending(user_a_id, user_b_id)

    return render_template("user_profile.html",
                           user=user,
                           total_friends=total_friends,
                           friends=friends,
                           pending_request=pending_request,
                           extra_completed=extra_completed)


@app.route("/setting", methods=["GET"])
def show_setting():
    return render_template("setting.html")


@app.route("/setting", methods=["POST"])
def setting():

    complete_age = request.form.get("complete_age")
    complete_gender = request.form.get("complete_gender")
    # print(session)
    mobile = request.form.get("mobile")
    address = request.form.get("address")
    city = request.form.get("city")
    placeOfBirth = request.form.get("placeOfBirth")
    interest = request.form.getlist("interest")
    occupation = request.form.get("occupation")
    
    netInterest = ','.join(interest)
    # for x in interest:
    #     netInterest = netInterest + ',' + x
    
    user_id = session["current_user"]["user_id"]
    user = db.session.query(User).filter(User.user_id == user_id).one()

    user.age = complete_age
    user.gender = complete_gender == 'male' and 'M' or 'F'

    user.mobile = mobile
    user.address = address
    user.city = city
    user.placeOfBirth = placeOfBirth
    user.interest = netInterest
    user.occupation = occupation

    db.session.commit()

    flash("Details Updated sucessfully", "success")

    return redirect("/users/%s" % user_id)

@app.route("/add-friend", methods=["POST"])
def add_friend():
    """Send a friend request to another user."""

    user_a_id = session["current_user"]["user_id"]
    user_b_id = request.form.get("user_b_id")

    print('User b id -------------', user_b_id)

    # Check connection status between user_a and user_b
    is_friends, is_pending = is_friends_or_pending(user_a_id, user_b_id)

    if user_a_id == user_b_id:
        return "You cannot add yourself as a friend."
    elif is_friends:
        return "You are already friends."
    elif is_pending:
        return "Your friend request is pending."
    else:
        requested_connection = Connection(user_a_id=user_a_id,
                                          user_b_id=user_b_id,
                                          status="Requested")
        db.session.add(requested_connection)
        db.session.commit()
        print("User ID %s has sent a friend request to User ID %s" % (user_a_id, user_b_id))
        return "Request Sent"


@app.route("/friends")
def show_friends_and_requests():
    """Show friend requests and list of all friends"""

    # This returns User objects for current user's friend requests
    received_friend_requests, sent_friend_requests = get_friend_requests(session["current_user"]["user_id"])

    # This returns a query for current user's friends (not User objects), but adding .all() to the end gets list of User objects
    friends = get_friends(session["current_user"]["user_id"]).all()

    return render_template("friends.html",
                           received_friend_requests=received_friend_requests,
                           sent_friend_requests=sent_friend_requests,
                           friends=friends)


@app.route("/friends/search", methods=["GET"])
def search_users():
    """Search for a user by email and return results."""

    # Returns users for current user's friend requests
    received_friend_requests, sent_friend_requests = get_friend_requests(session["current_user"]["user_id"])

    # Returns query for current user's friends (not User objects) so add .all() to the end to get list of User objects
    friends = get_friends(session["current_user"]["user_id"]).all()

    user_input = request.args.get("q")

    # Search user's query in users table of db and return all search results

    search_results = search(db.session.query(User), user_input).all()
    return render_template("friends_search_results.html",
                           received_friend_requests=received_friend_requests,
                           sent_friend_requests=sent_friend_requests,
                           friends=friends,
                           search_results=search_results)


@app.route("/suggest", methods=["POST"])
def suggest():
    """Suggest similar users based on columns."""

    user_id = session["current_user"]["user_id"]

    age = request.form.get("age")
    occupation = request.form.get("occupation")
    interests = request.form.get("interests")
    city = request.form.get("city")

    all_users = db.session.query(User).all()
    # age_sim, occ_sim, location_sim, interest_sim
    print('Currently all users - \n')
    print(all_users)
    user = db.session.query(User).filter(User.user_id == user_id).one()

    similarities = {}
    for user in all_users:
        similarities[user.user_id] = 0.0
    
    print('Similaritites - ')
    print(similarities)

    sim = 0
    for user_test in all_users:
        if age is not None:
            sim = age_sim(user_test.age, user.age)
            similarities[user_test.user_id] += sim
        
        if occupation is not None:
            sim = occ_sim(user_test.occupation, user.occupation)
            similarities[user_test.user_id] += sim
        
        if interests is not None:
            sim = interest_sim(user_test.interest, user.interest)
            similarities[user_test.user_id] += sim
        
        if city is not None:
            sim = location_sim(user_test.city, user.city)
            similarities[user_test.user_id] += sim
    
    # similarities filled
    similarities = sorted(similarities.items(), key = lambda kv:(kv[0], kv[1]))

    print(similarities)
    # summer sorted
    suggestions = []

    for key, value in similarities:
        print('Value - ', value)
        if (key == user_id):
            continue
        suggestions.append(key)
        if len(suggestions) == 10:
            break
    

    # flash("An account already exists with this email address. Please login.", "danger")
    to_friends = []
    for val in suggestions:
        user = db.session.query(User).filter(User.user_id == val).first()
        print('Got user - ', user.first_name)
        to_friends.append(user)

    return render_template("suggestions.html", users=to_friends)


@app.route("/error")
def error():
    raise Exception("Error!")


if __name__ == "__main__":
    # Set debug=True here to invoke the DebugToolbarExtension
    app.debug = True

    # connect_to_db(app)
    connect_to_db(app, os.environ.get("DATABASE_URL"))
    db.create_all()

    # Use the DebugToolbar
    #DebugToolbarExtension(app)

    PORT = int(os.environ.get("PORT", 5000))
    DEBUG = "NO_DEBUG" not in os.environ

    # app.run()
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG)

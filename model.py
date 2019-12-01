"""Models and database functions for decode."""

from flask_sqlalchemy import SQLAlchemy

import datetime

from sqlalchemy_searchable import make_searchable
from sqlalchemy_utils.types import TSVectorType

# This is the connection to the PostgreSQL database; we're getting this through
# the Flask-SQLAlchemy helper library. On this, we can find the `session`
# object, where we do most of our interactions (like committing, etc.)
db = SQLAlchemy()

make_searchable()


##############################################################################
# Model definitions

class User(db.Model):
    """User of decode website."""

    __tablename__ = "users"

    user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    # Put name inside TSVectorType definition for it to be fulltext-indexed (searchable)
    search_vector = db.Column(TSVectorType('first_name', 'last_name'))

    def __repr__(self):
        """Provide helpful representation when printed."""

        return "<User user_id=%s email=%s>" % (self.user_id,
                                               self.email)



class Connection(db.Model):
    """Connection between two users to establish a friendship and can see each other's info."""

    __tablename__ = "connections"

    connection_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_a_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    user_b_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    status = db.Column(db.String(100), nullable=False)

    # When both columns have a relationship with the same table, need to specify how
    # to handle multiple join paths in the square brackets of foreign_keys per below
    user_a = db.relationship("User", foreign_keys=[user_a_id], backref=db.backref("sent_connections"))
    user_b = db.relationship("User", foreign_keys=[user_b_id], backref=db.backref("received_connections"))

    def __repr__(self):
        """Provide helpful representation when printed."""

        return "<Connection connection_id=%s user_a_id=%s user_b_id=%s status=%s>" % (self.connection_id,
                                                                                      self.user_a_id,
                                                                                      self.user_b_id,
                                                                                      self.status)


##############################################################################
# Helper functions

def connect_to_db(app, db_uri=None):
    """Connect the database to our Flask app."""

    # Configure to use our PostgreSQL database
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri or 'postgresql:///breadcrumbs'
    app.config['SQLALCHEMY_ECHO'] = True
    db.app = app
    db.init_app(app)


if __name__ == "__main__":
    # As a convenience, if we run this module interactively, it will leave
    # you in a state of being able to work with the database directly.

    from server import app
    connect_to_db(app)
    print("Connected to DB.")

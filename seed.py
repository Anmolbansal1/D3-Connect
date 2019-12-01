"""Utility file to seed info from Yelp API into the breadcrumbs database"""

from sqlalchemy import func

from model import connect_to_db, db

from server import app



if __name__ == "__main__":
    connect_to_db(app)

    # Configure mappers before creating tables in order for search trigger in
    # SQLAlchemy-Searchable to work properly
    db.configure_mappers()

    # In case tables haven't been created, create them
    db.create_all()

    db.session.commit()

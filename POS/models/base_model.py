"""
    This module uses SQLAlchemy to create the database structures (if they do not exist)
    and exposes a database session object to be used by the app
"""

from flask import logging

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from ..constants import DATABASE_URL_ENV_NAME, DATABASE_URL

# Create the BaseModel model through which all other models will be declared
BaseModel = declarative_base()

# Import the various models

# noinspection PyUnresolvedReferences
from .user import User
# noinspection PyUnresolvedReferences
from .business import Business
# noinspection PyUnresolvedReferences
from .role import Role

try:
    db_engine = create_engine(DATABASE_URL)

    # Bind the engine to the models
    BaseModel.metadata.bind = db_engine

    # Create a session object to be used by the app to do any DB transaction
    Session = sessionmaker(
        bind=db_engine
    )

    db_session = Session()

    # Create all structures
    # BaseModel.metadata.drop_all()
    BaseModel.metadata.create_all()

    # Load default user roles
    default_roles = Role.load_roles_from_config()

    for role_id, role in default_roles.items():
        role_name = role["name"]
        role_description = role["description"]

        # Check if role already exists
        existing_role = db_session.query(Role).filter(
            Role.name == role_name
        ).first()

        # If it doesn't create it
        if not existing_role:
            role = Role(role_name, role_description)
            db_session.add(role)
            db_session.commit()

except AttributeError as attr_err:
    logger = logging.getLogger()
    logger.log(
        logging.ERROR,
        "%s attribute not found or provided" % DATABASE_URL_ENV_NAME
    )
    raise

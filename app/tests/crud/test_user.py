from fastapi.encoders import jsonable_encoder
from sqlmodel import Session

from app import crud
from app.core.security import verify_password
from app.models import User, UserCreate, UserUpdate
from app.tests.utils.utils import random_email, random_lower_string


def test_create_user(db: Session) -> None:
    """abc"""
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)
    assert user.email == email
    assert hasattr(user, "hashed_password")


def test_authenticate_user(db: Session) -> None:
    """
    Authenticates a random user using a generated email and password, creates the
    user in the database, and asserts that the authenticated user is the same as
    the created user.

    Args:
        db (Session): database session, which is used to perform CRUD (Create,
            Read, Update, Delete) operations on the user data.

    """
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)
    authenticated_user = crud.authenticate(
        session=db, email=email, password=password)
    assert authenticated_user
    assert user.email == authenticated_user.email


def test_not_authenticate_user(db: Session) -> None:
    """
    Attempts to authenticate a random email and password combination but fails due
    to the user not being authenticated, returning `None`.

    Args:
        db (Session): Session object that contains the database connection for the
            application.

    """
    email = random_email()
    password = random_lower_string()
    user = crud.authenticate(session=db, email=email, password=password)
    assert user is None


def test_check_if_user_is_active(db: Session) -> None:
    """
    Verifies if a newly created user is active by checking their `is_active` attribute.

    Args:
        db (Session): session object that provides access to the database for
            performing CRUD operations, including creating a new user.

    """
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)
    assert user.is_active is True


def test_check_if_user_is_active_inactive(db: Session) -> None:
    """
    Verifies that a newly created user is marked as active in the database after
    creation.

    Args:
        db (Session): Session object that is used to interact with the database
            and retrieve data.

    """
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, disabled=True)
    user = crud.create_user(session=db, user_create=user_in)
    assert user.is_active


def test_check_if_user_is_superuser(db: Session) -> None:
    """
    Tests whether a newly created user is marked as a superuser by verifying the
    `is_superuser` attribute of the resulting user object.

    Args:
        db (Session): Python `Session` object that provides a connection to the
            database used for storing and retrieving data.

    """
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, is_superuser=True)
    user = crud.create_user(session=db, user_create=user_in)
    assert user.is_superuser is True


def test_check_if_user_is_superuser_normal_user(db: Session) -> None:
    """
    Tests whether a newly created user is a superuser or a normal user using the
    `is_superuser` attribute.

    Args:
        db (Session): Python `Session` object that provides a connection to the
            database, which is used to create and manipulate user objects within
            the function.

    """
    username = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=username, password=password)
    user = crud.create_user(session=db, user_create=user_in)
    assert user.is_superuser is False


def test_get_user(db: Session) -> None:
    """
    Tests the `get()` method of a Session instance, retrieving a User object and
    verifying its properties match those of the original User create call.

    Args:
        db (Session): Session object, which is used to interact with the database
            and perform CRUD operations such as creating and retrieving users.

    """
    password = random_lower_string()
    username = random_email()
    user_in = UserCreate(email=username, password=password, is_superuser=True)
    user = crud.create_user(session=db, user_create=user_in)
    user_2 = db.get(User, user.id)
    assert user_2
    assert user.email == user_2.email
    assert jsonable_encoder(user) == jsonable_encoder(user_2)


def test_update_user(db: Session) -> None:
    """
    Updates an existing user's password and checks the updated user's email, hashed
    password, and verifies the new password using `verify_password` function.

    Args:
        db (Session): session object of the database system used for creating and
            updating user objects.

    """
    password = random_lower_string()
    email = random_email()
    user_in = UserCreate(email=email, password=password, is_superuser=True)
    user = crud.create_user(session=db, user_create=user_in)
    new_password = random_lower_string()
    user_in_update = UserUpdate(password=new_password, is_superuser=True)
    if user.id is not None:
        crud.update_user(session=db, db_user=user, user_in=user_in_update)
    user_2 = db.get(User, user.id)
    assert user_2
    assert user.email == user_2.email
    assert verify_password(new_password, user_2.hashed_password)

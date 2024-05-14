from typing import Any

from sqlmodel import Session, select

from app.core.security import get_password_hash, verify_password
from app.models import Item, ItemCreate, User, UserCreate, UserUpdate


def create_user(*, session: Session, user_create: UserCreate) -> User:
    """
    Creates a new user instance by validating input data using the `User.model_validate()`
    method, hashing the password using the `get_password_hash()` method, and adding
    it to a session for persistence.

    Args:
        session (Session): Python `Session` object, which is used to interact with
            the database and persist the newly created user object after it has
            been validated and hashed password generated.
        user_create (UserCreate): user object to be created, which contains the
            attributes and values that will be used to create a new user in the
            database when the function is called.

    Returns:
        User: a validated User object.

    """
    db_obj = User.model_validate(
        user_create, update={
            "hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    """
    Updates a User object in a database by setting its attributes based on a user
    update object and storing it in the session.

    Args:
        session (Session): Session instance that will be used to persist the updated
            user data to the database after the update operation is completed.
        db_user (User): User instance to be updated, which is passed through to
            the `sqlmodel_update()` method to update its attributes and then added
            to the session for persistence.
        user_in (UserUpdate): UserUpdate object containing the data to be updated
            in the database.

    Returns:
        Any: a `User` object that has been updated with the provided data.

    """
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    """
    Retrieves a user from a database based on their email address using a SQL query
    selected by the `session` parameter.

    Args:
        session (Session): database session, which is used to execute the query
            to retrieve the user from the database.
        email (str): email address of the user to retrieve from the database.

    Returns:
        User | None: a User object or None if no user is found with the provided
        email address.

    """
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    """
    Verifies the authenticity of a user by checking their email address and password
    against the database. If successful, it returns the User object, otherwise it
    returns None.

    Args:
        session (Session): Session instance that is used to authenticate the user.
        email (str): email address of the user to be authenticated.
        password (str): password provided by the user for authentication verification.

    Returns:
        User | None: a `User` object if the email and password are valid, otherwise
        `None`.

    """
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user


def create_item(*, session: Session, item_in: ItemCreate, owner_id: int) -> Item:
    """
    Creates a new item object in a database by validating input data, adding it
    to the session, committing the changes, and retrieving the newly created item.

    Args:
        session (Session): database session object, which is used to interact with
            the database and perform CRUD (Create, Read, Update, Delete) operations
            on the items.
        item_in (ItemCreate): item to be created or updated in the database, and
            it is used to validate and modify its properties before adding it to
            the session.
        owner_id (int): ID of the user who will own the newly created item.

    Returns:
        Item: an instance of the `Item` model, which has been created and added
        to the session.

    """
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item

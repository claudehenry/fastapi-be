from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import Item, ItemCreate, ItemPublic, ItemsPublic, ItemUpdate, Message

router = APIRouter()


@router.get("/", response_model=ItemsPublic)
def read_items(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieves items from a database based on user permissions. It retrieves the
    number of items and returns both the items and the total number of items for
    a given user.

    Args:
        session (SessionDep): database session object used for executing SQL queries
            and retrieving data from the database.
        current_user (CurrentUser): current user accessing the items and is used
            to filter the items retrieved based on the user's identity.
        skip (0): 0-based offset from the beginning of the result set that the
            function should start retrieving items from.
        limit (100): maximum number of items to retrieve from the database for the
            specified user, and it determines the number of items returned in the
            response.

    Returns:
        Any: a `ItemsPublic` object containing the retrieved item data and its count.

    """

    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(Item)
        count = session.exec(count_statement).one()
        statement = select(Item).offset(skip).limit(limit)
        items = session.exec(statement).all()
    else:
        count_statement = (
            select(func.count())
            .select_from(Item)
            .where(Item.owner_id == current_user.id)
        )
        count = session.exec(count_statement).one()
        statement = (
            select(Item)
            .where(Item.owner_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )
        items = session.exec(statement).all()

    return ItemsPublic(data=items, count=count)


@router.get("/{id}", response_model=ItemPublic)
def read_item(session: SessionDep, current_user: CurrentUser, id: int) -> Any:
    """
    Retrieves an item by its ID from a database session and validates the user's
    permissions to access it.

    Args:
        session (SessionDep): SessionDependency object, which provides access to
            a session that can be used to retrieve an item by its ID.
        current_user (CurrentUser): current user making the request and is used
            to check if they have sufficient permissions to access the item being
            retrieved.
        id (int): ID of the item to be retrieved from the session.

    Returns:
        Any: an instance of the `Item` class.

    """
    item = session.get(Item, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return item


@router.post("/", response_model=ItemPublic)
def create_item(
    *, session: SessionDep, current_user: CurrentUser, item_in: ItemCreate
) -> Any:
    """
    Creates a new item by validating its input, updating its owner ID to the current
    user's ID, adding it to the session, and committing the changes to the database.
    It then refreshes the newly created item for further processing.

    Args:
        session (SessionDep): database session that is used to add, commit, and
            refresh the newly created item.
        current_user (CurrentUser): owner of the newly created item, and its value
            is used to update the `owner_id` field of the item being created in
            the database.
        item_in (ItemCreate): item to be created, which is validated and updated
            with the current user's id before being added to the session and committed.

    Returns:
        Any: an instance of the `Item` model, newly created and added to the session
        for commitment and refresh.

    """
    item = Item.model_validate(item_in, update={"owner_id": current_user.id})
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.put("/{id}", response_model=ItemPublic)
def update_item(
    *, session: SessionDep, current_user: CurrentUser, id: int, item_in: ItemUpdate
) -> Any:
    """
    Updates an item in a SQL database based on input from the user, ensuring that
    only authorized users can perform the update and providing a way to refresh
    the updated item after the update has been committed to the database.

    Args:
        session (SessionDep): SessionDep object, which is used to interact with
            the database and perform operations such as getting and updating items.
        current_user (CurrentUser): current user making the request, and is used
            to check if the user has sufficient permissions to update the item.
        id (int): ID of the item to be updated.
        item_in (ItemUpdate): `ItemUpdate` instance that contains the updates to
            be applied to the item.

    Returns:
        Any: an updated item object.

    """
    item = session.get(Item, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    update_dict = item_in.model_dump(exclude_unset=True)
    item.sqlmodel_update(update_dict)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/{id}")
def delete_item(session: SessionDep, current_user: CurrentUser, id: int) -> Message:
    """
    Deletes an item from a session, checking for the item's existence and the
    user's permissions before deleting it.

    Args:
        session (SessionDep): database session to which the item to be deleted belongs.
        current_user (CurrentUser): current user accessing the function and is
            used to check if they have sufficient permissions to delete an item.
        id (int): ID of the item to be deleted.

    Returns:
        Message: a message indicating that the item has been deleted successfully.

    """
    item = session.get(Item, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    session.delete(item)
    session.commit()
    return Message(message="Item deleted successfully")

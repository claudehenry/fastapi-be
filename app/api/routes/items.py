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
    Retrieves items based on user permissions, returning a list of items and their
    counts.

    Args:
        session (SessionDep): 3Arcade SessionDependency object, which provides the
            session for executing the database queries and retrieving the items.
        current_user (CurrentUser): current user who is requesting the items.
        skip (0): 0-based offset from the beginning of the items list that the
            function should skip when retrieving data.
        limit (100): maximum number of items to be retrieved from the database for
            each page of results.

    Returns:
        Any: a list of `Item` objects and their count.

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
    Retrieves an item by its ID, checks if the user has sufficient permissions to
    access it, and returns the item if found or raises an exception if not.

    Args:
        session (SessionDep): SessionDependency object, which provides access to
            the session state and allows the function to retrieve items from the
            session.
        current_user (CurrentUser): current user making the request and is used
            to check if they have sufficient permissions to access the item being
            retrieved.
        id (int): ID of the item to be retrieved from the session.

    Returns:
        Any: an `Item` object.

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
    Creates a new item by validating its input, adding it to the session, committing
    the changes, and refreshing the newly created item.

    Args:
        session (SessionDep): SessionDep object, which is used to perform database
            operations such as adding and committing new data to the database.
        current_user (CurrentUser): user who is performing the action of creating
            a new item, and it is used to set the owner ID of the newly created
            item to that user's ID.
        item_in (ItemCreate): data to be used to create a new item.

    Returns:
        Any: a newly created item object with its attributes validated and updated
        based on the input parameters.

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
    Updates an existing item in a database by checking its existence, verifying
    the user's permissions, and applying the specified update using SQLModel.

    Args:
        session (SessionDep): SessionDep class instance, which provides the session
            for accessing and modifying data in the database.
        current_user (CurrentUser): current user making the request and checks if
            they have sufficient permissions to update the item.
        id (int): ID of the item to be updated.
        item_in (ItemUpdate): update data for the item to be updated, which is
            used to modify the item's attributes through a `model_dump()` method
            call before saving it back to the database using the `sqlmodel_update()`
            method.

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
    Deletes an item from a database based on its ID, checks if the user has
    sufficient permissions and raises an exception if not.

    Args:
        session (SessionDep): Session object, which provides the functionality for
            accessing and manipulating data in the database.
        current_user (CurrentUser): current user accessing the function and is
            used to verify if the user has enough permissions to delete an item.
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

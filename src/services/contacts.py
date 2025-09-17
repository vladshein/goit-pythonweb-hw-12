from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from src.repository.contacts import ContactRepository
from src.schemas.contacts import ContactModel
from src.db.models import User


def _handle_integrity_error(e: IntegrityError):
    """
    Handle integrity errors and raise corresponding appropriate HTTPException.

    If the error is caused by a unique constraint on the tag and user,
    raise a 409 Conflict error with a detail indicating that a tag with the same name already exists for the user.

    Otherwise, raise a 400 Bad Request error with a detail indicating that the data is invalid.

    :param e: The integrity error to handle.
    :raises HTTPException: A 409 Conflict or 400 Bad Request error.
    """
    if "unique_tag_user" in str(e.orig):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Тег з такою назвою вже існує.",
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Помилка цілісності даних.",
        )


class ContactsService:
    def __init__(self, db: AsyncSession):
        self.contacts_repository = ContactRepository(db)

    async def create_contact(self, body: ContactModel, user: User):
        """
        Create a new contact.

        Args:
            body (ContactModel): Contact data to create contact with.
            user (User): Current user.

        Returns:
            Contact: Created contact.

        Raises:
            HTTPException: If contact not found.
        """
        try:
            return await self.contacts_repository.create_contact(body, user)
        except IntegrityError as e:
            await self.contacts_repository.db.rollback()
            _handle_integrity_error(e)

    async def get_contacts(self, skip: int, limit: int, query_params: dict, user: User):
        """
        Get a list of contacts filtered by the given query parameters.

        Args:
            skip (int): Number of records to skip.
            limit (int): Maximum number of records to return.
            query_params (dict): Dictionary of query parameters to filter contacts by.
            user (User): Current user.

        Returns:
            List[Contact]: List of contacts filtered by the given query parameters.
        """
        return await self.contacts_repository.get_contacts(
            skip, limit, query_params, user
        )

    async def get_contact(self, contact_id: int, user: User):
        """
        Get a contact by its ID.

        Args:
            contact_id (int): Contact ID to retrieve.
            user (User): Current user.

        Returns:
            Contact | None: Contact with the given ID, or None if not found.
        """
        return await self.contacts_repository.get_contact_by_id(contact_id, user)

    # TODO: check body to be processed
    async def update_contact(self, contact_id: int, body: ContactModel, user: User):
        """
        Update a contact by its ID.

        Args:
            contact_id (int): Contact ID to update.
            body (ContactModel): Contact data to update contact with.
            user (User): Current user.

        Returns:
            Contact | None: Updated contact, or None if not found.
        """
        return await self.contacts_repository.update_contact(contact_id, body, user)

    async def remove_contact(self, contact_id: int, user: User):
        """
        Remove a contact by its ID.

        Args:
            contact_id (int): Contact ID to remove.
            user (User): Current user.

        Returns:
            Contact | None: Contact with the given ID, or None if not found.
        """
        return await self.contacts_repository.remove_contact(contact_id, user)

    async def get_contacts_with_upcoming_birthdays(self, user: User):
        """
        Get a list of contacts with upcoming birthdays within the next 7 days.

        Args:
            user (User): Current user.

        Returns:
            List[Contact]: List of contacts with upcoming birthdays.
        """
        return await self.contacts_repository.get_contacts_with_upcoming_birthdays(user)

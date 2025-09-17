from typing import List
from datetime import date, timedelta


from sqlalchemy import select, extract, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Contact, User
from src.schemas.contacts import ContactModel


class ContactRepository:
    def __init__(self, session: AsyncSession):
        """
        Initialize ContactRepository with a database session.

        Args:
            session (AsyncSession): Database session to use for database operations.
        """
        self.db = session

    async def get_contacts(
        self, skip: int, limit: int, query: dict, user: User
    ) -> List[Contact]:
        # stmt = select(Contact).filter_by(**query).offset(skip).limit(limit)
        # check filter by user and filter by query
        """
        Get a list of contacts filtered by the given query parameters.

        Args:
            skip (int): Number of records to skip.
            limit (int): Maximum number of records to return.
            query (dict): Dictionary of query parameters to filter contacts by.
            user (User): Current user.

        Returns:
            List[Contact]: List of contacts filtered by the given query parameters.
        """
        stmt = select(Contact).filter_by(**query, user=user).offset(skip).limit(limit)
        contacts = await self.db.execute(stmt)
        return contacts.scalars().all()

    async def get_contact_by_id(self, contact_id: int, user: User) -> Contact | None:
        """
        Get a contact by its ID.

        Args:
            contact_id (int): Contact ID to retrieve.
            user (User): Current user.

        Returns:
            Contact | None: Contact with the given ID, or None if not found.
        """
        stmt = select(Contact).filter_by(id=contact_id, user=user)
        contact = await self.db.execute(stmt)
        return contact.scalar_one_or_none()

    async def create_contact(self, body: ContactModel, user: User) -> Contact:
        """
        Create a new contact.

        Args:
            body (ContactModel): Contact data to create contact with.
            user (User): Current user.

        Returns:
            Contact: Created contact.
        """
        contact = Contact(**body.model_dump(exclude_unset=True), user=user)
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return await self.get_contact_by_id(contact.id)

    async def remove_contact(self, contact_id: int, user: User) -> Contact | None:
        """
        Remove a contact by its ID.

        Args:
            contact_id (int): Contact ID to remove.
            user (User): Current user.

        Returns:
            Contact | None: Contact with the given ID, or None if not found.
        """
        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            await self.db.delete(contact)
            await self.db.commit()
        return contact

    async def update_contact(
        self, note_id: int, body: ContactModel, user: User
    ) -> Contact | None:
        """
        Update a contact by its ID.

        Args:
            note_id (int): Contact ID to update.
            body (ContactModel): Contact data to update contact with.
            user (User): Current user.

        Returns:
            Contact | None: Updated contact, or None if not found.
        """
        contact = await self.get_contact_by_id(note_id, user)
        if contact:
            for key, value in body.dict(exclude_unset=True).items():
                setattr(contact, key, value)

            await self.db.commit()
            await self.db.refresh(contact)

        return contact

    async def get_contacts_with_upcoming_birthdays(self, user: User) -> List[Contact]:
        """
        Get a list of contacts with upcoming birthdays within the next 7 days.

        Args:
            user (User): Current user.

        Returns:
            List[Contact]: List of contacts with upcoming birthdays.
        """
        today = date.today()
        future_date = today + timedelta(days=7)
        stmt = select(Contact).filter(
            and_(
                extract("month", Contact.birthday) >= today.month,
                extract("day", Contact.birthday) >= today.day,
                extract("month", Contact.birthday) <= future_date.month,
                extract("day", Contact.birthday) <= future_date.day,
            ),
            user=user,
        )
        contacts = await self.db.execute(stmt)
        return contacts.scalars().all()

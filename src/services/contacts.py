from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from src.repository.contacts import ContactRepository
from src.schemas.contacts import ContactModel
from src.db.models import User


def _handle_integrity_error(e: IntegrityError):
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
        try:
            return await self.contacts_repository.create_contact(body, user)
        except IntegrityError as e:
            await self.contacts_repository.db.rollback()
            _handle_integrity_error(e)

    async def get_contacts(self, skip: int, limit: int, query_params: dict, user: User):
        return await self.contacts_repository.get_contacts(
            skip, limit, query_params, user
        )

    async def get_contact(self, contact_id: int, user: User):
        return await self.contacts_repository.get_contact_by_id(contact_id, user)

    # TODO: check body to be processed
    async def update_contact(self, contact_id: int, body: ContactModel, user: User):
        return await self.contacts_repository.update_contact(contact_id, body, user)

    async def remove_contact(self, contact_id: int, user: User):
        return await self.contacts_repository.remove_contact(contact_id, user)

    async def get_contacts_with_upcoming_birthdays(self, user: User):
        return await self.contacts_repository.get_contacts_with_upcoming_birthdays(user)

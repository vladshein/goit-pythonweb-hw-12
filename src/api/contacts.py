from typing import List

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import EmailStr
from src.schemas.contacts import ContactModel, ContactResponse
from src.services.contacts import ContactsService
from src.db.models import User
from src.db.connection import get_db
from src.services.auth import get_current_user


router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("/")
async def get_contacts(
    first_name: str | None = None,
    last_name: str | None = None,
    email: EmailStr | None = None,
    phone_number: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    response_model=List[ContactResponse],
    user: User = Depends(get_current_user),
):
    contact_service = ContactsService(db)
    query_params = {}
    if first_name:
        query_params["first_name"] = first_name
    if last_name:
        query_params["last_name"] = last_name
    if email:
        query_params["email"] = email
    if phone_number:
        query_params["phone_number"] = phone_number
    contacts = await contact_service.get_contacts(skip, limit, query_params, user)
    return contacts


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    contact_service = ContactsService(db)
    contact = await contact_service.get_contact(contact_id, user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return contact


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def add_contact(
    body: ContactModel,
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    contacts_service = ContactsService(db)
    return await contacts_service.create_contact(body, user)


@router.delete("/{contact_id}", response_model=ContactResponse)
async def add_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    contact_service = ContactsService(db)
    contact = await contact_service.remove_contact(contact_id, user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Requested contact not found"
        )
    return contact


@router.patch("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    body: ContactModel,
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    contact_service = ContactsService(db)
    contact = await contact_service.update_contact(contact_id, body, user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Note not found"
        )
    return contact


@router.get("/upcoming_birthdays/", response_model=List[ContactResponse])
async def coming_birthday_contacts(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    contact_service = ContactsService(db)
    return await contact_service.get_contacts_with_upcoming_birthdays(user)

from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar

from src.repository.users import UserRepository
from src.schemas.contacts import UserCreate


class UserService:
    def __init__(self, db: AsyncSession):
        """
        Initialize the UserService with a database session.

        Args:
            db (AsyncSession): Database session to use for database operations.
        """
        self.repository = UserRepository(db)

    async def create_user(self, body: UserCreate):
        """
        Create a new user.

        Args:
            body (UserCreate): User data to create user with.

        Returns:
            User: Created user.
        """
        avatar = None
        try:
            g = Gravatar(body.email)
            avatar = g.get_image()
        except Exception as e:
            print(e)

        return await self.repository.create_user(body, avatar)

    async def get_user_by_id(self, user_id: int):
        """
        Get a user by its id.

        Args:
            user_id (int): User id to retrieve.

        Returns:
            User | None: User with the given id, or None if not found.
        """
        return await self.repository.get_user_by_id(user_id)

    async def get_user_by_username(self, username: str):
        """
        Get a user by its username.

        Args:
            username (str): Username of the user to retrieve.

        Returns:
            User | None: User with the given username, or None if not found.
        """
        return await self.repository.get_user_by_username(username)

    async def get_user_by_email(self, email: str):
        """
        Get a user by its email address.

        Args:
            email (str): Email address of the user to retrieve.

        Returns:
            User | None: User with the given email address, or None if not found.
        """
        return await self.repository.get_user_by_email(email)

    async def confirmed_email(self, email: str):
        """
        Confirm email address of the user.

        Args:
            email (str): Email address to confirm.

        Returns:
            None
        """
        return await self.repository.confirmed_email(email)

    async def update_avatar_url(self, email: str, url: str):
        """
        Update avatar URL of the user.

        Args:
            email (str): Email address of the user to update.
            url (str): New avatar URL of the user.

        Returns:
            None
        """
        return await self.repository.update_avatar_url(email, url)

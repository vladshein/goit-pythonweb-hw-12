import contextlib
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

# from src.conf.config import config
from src.conf.config import settings


class DatabaseSessionManager:
    def __init__(self, url: str):
        """
        Initialize the database session manager.

        Parameters
        ----------
        url : str
            The database URL

        Attributes
        ----------
        _engine : AsyncEngine | None
            The database engine
        _session_maker : async_sessionmaker
            The session maker
        """
        self._engine: AsyncEngine | None = create_async_engine(url)
        self._session_maker: async_sessionmaker = async_sessionmaker(
            autoflush=False, autocommit=False, bind=self._engine
        )

    @contextlib.asynccontextmanager
    async def session(self):
        """
        Context manager to handle database sessions.

        This context manager is used to create a database session and
        handle exceptions, rollback and close the session.

        If the session maker is not initialized, it raises an exception.

        If a SQLAlchemyError occurs, it rolls back the session and re-raises
        the original error.

        Finally, it closes the session.

        Use this context manager as follows:
        async with self.session() as session:
            # Do something with the session
        """
        if self._session_maker is None:
            raise Exception("Database session is not initialized")
        session = self._session_maker()
        try:
            yield session
        except SQLAlchemyError as e:
            await session.rollback()
            raise  # Re-raise the original error
        finally:
            await session.close()


sessionmanager = DatabaseSessionManager(settings.DB_URL)


async def get_db():
    """
    Async generator that yields a database session.

    This generator is used to create a database session and handle exceptions,
    rollback and close the session.

    If the session maker is not initialized, it raises an exception.

    If a SQLAlchemyError occurs, it rolls back the session and re-raises
    the original error.

    Finally, it closes the session.

    Use this context manager as follows:
    async with get_db() as session:
        # Do something with the session
    """
    async with sessionmanager.session() as session:
        yield session


# test connection
# async def test_connection():
#     db_session_gen = get_db()
#     db_session = await anext(db_session_gen)
#     result = await db_session.execute(text("SELECT 1 + 1"))
#     print(result.scalar())


# asyncio.run(test_connection())

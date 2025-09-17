from datetime import datetime
from enum import Enum

from sqlalchemy import Column, Integer, String, func, Boolean, Enum as SqlEnum
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql.sqltypes import DateTime, Date
from sqlalchemy.sql.schema import ForeignKey, UniqueConstraint


class Base(DeclarativeBase):
    pass


class UserRole(str, Enum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


class Contact(Base):
    __tablename__ = "contacts"
    # check user name and its uniqueness
    # __table_args__ = (UniqueConstraint("name", "user_id", name="unique_user"),)

    def __repr__(self):
        return f"#Contact(id={self.id}, name={self.first_name} {self.last_name}, email={self.email})"

    def __str__(self):
        return f"#Contact(id={self.id}, name={self.first_name} {self.last_name}, email={self.email})"

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(120), nullable=False)
    last_name = Column(String(120), nullable=False)
    email = Column(String(120), nullable=False)
    phone_number = Column(String(15), nullable=False)
    birthday = Column(Date)
    user_id = Column(
        "user_id", ForeignKey("users.id", ondelete="CASCADE"), default=None
    )
    user = relationship("User", backref="contacts")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=func.now())
    avatar = Column(String(255), nullable=True)
    confirmed = Column(Boolean, default=False)
    # role = Column(SqlEnum(UserRole), default=UserRole.USER, nullable=False)
    role = Column(
        SqlEnum(UserRole, name="userrole"), default=UserRole.USER, nullable=False
    )

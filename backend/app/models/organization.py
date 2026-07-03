from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TimestampedBase


class Organization(TimestampedBase):
    """Nivel raiz da hierarquia (ex.: Consominas)."""

    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), unique=True)

    contracts: Mapped[list["Contract"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    users: Mapped[list["User"]] = relationship(back_populates="organization")

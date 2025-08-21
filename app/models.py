from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Numeric, ForeignKey, Text, BigInteger, SmallInteger, TIMESTAMP, func
from typing import Optional, List

class Base(DeclarativeBase):
    pass

class Provider(Base):
    __tablename__ = "providers"
    provider_id: Mapped[str] = mapped_column(String, primary_key=True)
    provider_name: Mapped[str] = mapped_column(Text)
    provider_city: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    provider_state: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    provider_zip_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    prices: Mapped[List["DrgPrice"]] = relationship(back_populates="provider")
    ratings: Mapped[List["Rating"]] = relationship(back_populates="provider")

class DrgPrice(Base):
    __tablename__ = "drg_prices"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    provider_id: Mapped[str] = mapped_column(ForeignKey("providers.provider_id", ondelete="CASCADE"))
    ms_drg_definition: Mapped[str] = mapped_column(Text)
    ms_drg_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_discharges: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    average_covered_charges: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    average_total_payments: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    average_medicare_payments: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    provider: Mapped["Provider"] = relationship(back_populates="prices")

class Rating(Base):
    __tablename__ = "ratings"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    provider_id: Mapped[str] = mapped_column(ForeignKey("providers.provider_id", ondelete="CASCADE"))
    rating: Mapped[int] = mapped_column(SmallInteger)
    created_at: Mapped[Optional[str]] = mapped_column(TIMESTAMP, server_default=func.now())
    provider: Mapped["Provider"] = relationship(back_populates="ratings")

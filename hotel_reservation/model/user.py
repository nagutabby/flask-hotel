from dataclasses import dataclass

from sqlalchemy import *

from hotel_reservation.model.base import Base

@dataclass
class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    age = Column(String, unique=True)

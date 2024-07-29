from dataclasses import dataclass

from sqlalchemy import *

from hotel_reservation.model.base import Base

@dataclass
class Reservation(Base):
    __tablename__ = 'reservation'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    start_date = Column(Date)
    end_date = Column(Date)
    number_rooms = Column(Integer)

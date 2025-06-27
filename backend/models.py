#Data models

from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import Enum
import enum

class SlotStatus(enum.Enum):
    Available = "Available"
    Occupied = "Occupied"

db=SQLAlchemy()

#First entity
class User_Info(db.Model):
    __tablename__="user_info"
    id=db.Column(db.Integer,primary_key=True)
    email=db.Column(db.String,unique=True,nullable=False)
    password=db.Column(db.String,nullable=False)
    role=db.Column(db.Integer,default=1) 
    full_name=db.Column(db.String,nullable=False)
    address=db.Column(db.String,nullable=False)
    pin_code=db.Column(db.Integer,nullable=False)
    vehicle_no=db.Column(db.String,nullable=False)
    reservations=db.relationship("Reservation",cascade="all,delete",backref="user_info",lazy=True) #User can access all of his/her reservations

    
#Entity2
class ParkingLot(db.Model):
    __tablename__="parkinglot"
    id=db.Column(db.Integer,primary_key=True)
    prime_location_name=db.Column(db.String,nullable=False)
    location=db.Column(db.String,nullable=False)
    tkt_price=db.Column(db.Float,default=0.0)
    pin_code=db.Column(db.Integer,nullable=False)
    capacity=db.Column(db.Integer,nullable=False)
    venue_pic_url=db.Column(db.String,nullable=True,default="None")
    slots=db.relationship("Slot",cascade="all,delete",backref="parkinglot",lazy=True) #plot can access all of its slots

#Entity3 table
class Slot(db.Model):
    __tablename__="slot"
    id=db.Column(db.Integer,primary_key=True)
    status = db.Column(Enum(SlotStatus), default=SlotStatus.Available)
    parkinglot_id=db.Column(db.Integer, db.ForeignKey("parkinglot.id"),nullable=False)
    reservations=db.relationship("Reservation",cascade="all,delete",backref="slot",lazy=True) #Slot can access reservation
  

#Entity4 
class Reservation(db.Model):
    __tablename__="reservation"
    id=db.Column(db.Integer,primary_key=True)
    parking_timestamp=db.Column(db.DateTime,nullable=False)
    leaving_timestamp=db.Column(db.DateTime,nullable=True)
    user_rating=db.Column(db.Integer,default=0)
    parking_cost=db.Column(db.Float,default=0.0)
    user_id=db.Column(db.Integer, db.ForeignKey("user_info.id"),nullable=False)
    slot_id=db.Column(db.Integer, db.ForeignKey("slot.id"),nullable=False)





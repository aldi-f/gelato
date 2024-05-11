from os import path
import logging
from sqlalchemy import create_engine
from sqlalchemy import String, ForeignKey, Integer
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy.orm import sessionmaker, scoped_session

logger = logging.getLogger(__name__)

DATABASE_PATH = "/data/gelato.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
session_factory = sessionmaker(engine)
Session = scoped_session(session_factory)


class Base(DeclarativeBase):
    pass


class Servers(Base):
    __tablename__ = "servers"

    server_id = mapped_column(String(20), primary_key=True)
    server_name = mapped_column(String(30), nullable=True)
    total_videos = mapped_column(Integer, default=0)
    total_storage = mapped_column(Integer,  default=0)
    convert_relate = relationship("Convert", back_populates="server_relate")
    

class Convert(Base):
    __tablename__ = "convert"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    server_id = mapped_column(String(30), ForeignKey('servers.server_id'))
    user_id = mapped_column(String(30))
    source = mapped_column(String(30))
    download_size = mapped_column(Integer)

    server_relate = relationship("Servers", back_populates="convert_relate")


def init_db():
    with engine.connect(): # just to start it
        Base.metadata.create_all(engine)
    
from typing import Annotated
from fastapi import Depends
from sqlmodel import SQLModel, create_engine, Session

sqlite_file_name = "database/bionet.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def get_session():
    with Session(engine) as session:
        yield session


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


SessionDep = Annotated[Session, Depends(get_session)]


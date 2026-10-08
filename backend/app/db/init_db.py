from app.db.base import Base
from app.db.session import engine

# Import models so SQLAlchemy knows about them
from app.db import models


def init_db():
    Base.metadata.create_all(bind=engine)

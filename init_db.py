from database import engine
from models.db_models import Base

# Create all tables in database
Base.metadata.create_all(bind=engine)

print("Tables created successfully!")
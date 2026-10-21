import sys, os
current = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current)

from apps.models.db_models import Base, engine

Base.metadata.create_all(engine)
print("Tables created.")
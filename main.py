from fastapi import FastAPI
from sql import models
from sql.database import engine
import api.v1

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(api.v1.router)

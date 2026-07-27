import sys
import os
import certifi

ca=certifi.where()

from dotenv import load_dotenv
load_dotenv()

mongo_db_uri=os.getenv("URI")
print(mongo_db_uri)
import pymongo
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
from networksecurity.pipeline.training_pipeline import TrainingPipeline
from networksecurity.contants.training_pipeline import DATA_INGESTION_DATABASE_NAME,DATA_INGESTION_COLLECTION_NAME
from networksecurity.utils.main_utils.utils import load_object
from networksecurity.utils.ml_utils.model.estimator import NetworkModel
from networksecurity.pipeline.batch_prediction import BatchPipeline
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI,File,UploadFile,Request
from uvicorn import run as app_run

from fastapi.responses import Response
from starlette.responses import RedirectResponse
import pandas as pd



client=pymongo.MongoClient(mongo_db_uri)

database=client[DATA_INGESTION_DATABASE_NAME]
collection=client[DATA_INGESTION_COLLECTION_NAME]

app=FastAPI()
origins=["*"]

app.add_middleware(
    CORSMiddleware,
    allow_methods=["*"],
    allow_credentials=True,
    allow_headers=["*"],
    allow_origins=origins
)

from fastapi.templating import Jinja2Templates
templates= Jinja2Templates(directory="templates")

@app.get("/",tags=["authentication"])
async def index():
    return RedirectResponse(url="/docs")

@app.get("/train")
async def train_route():
    try:
        train_pipeline=TrainingPipeline()
        train_pipeline.run_pipeline()
        return Response("Training is sucessfull")
    except Exception as e:
        raise NetworkSecurityException(e,sys)
@app.post("/predict")
async def predict_route(request:Request,file:UploadFile=File(...)):
    try:
        batch_pipeline=BatchPipeline()
        table_html=batch_pipeline.run_prediciton(file)

        return templates.TemplateResponse(
            request=request,
            name="table.html",
            context={"table": table_html},
        )
    except Exception as e:
        raise NetworkSecurityException(e,sys)


if __name__=="__main__":
    app_run(app,host="localhost",port=8000)
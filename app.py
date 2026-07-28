import sys
import os
import time
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
from fastapi.responses import JSONResponse
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

FINAL_MODEL_DIR = "final_model"
DATASET_PATH = os.path.join("Network_Data", "phisingData.csv")

# Result column convention for this dataset: 1 = legitimate site, -1 = phishing site.
VERDICT_LABELS = {1: "Legitimate", -1: "Phishing", 0: "Suspicious"}


@app.exception_handler(NetworkSecurityException)
async def network_security_exception_handler(request: Request, exc: NetworkSecurityException):
    """
    Turns internal pipeline failures into a clean JSON body the dashboard
    can show as an error banner, instead of a raw traceback page.
    """
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.get("/",tags=["ui"])
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})


@app.get("/status",tags=["ui"])
async def status_route():
    """
    Lightweight, read-only snapshot the dashboard polls to know whether a
    trained model is available yet, and to show real dataset stats.
    """
    model_path = os.path.join(FINAL_MODEL_DIR, "model.pkl")
    preprocessor_path = os.path.join(FINAL_MODEL_DIR, "preprocessor.pkl")
    model_ready = os.path.exists(model_path) and os.path.exists(preprocessor_path)

    trained_at = None
    if model_ready:
        trained_at = int(os.path.getmtime(model_path))

    dataset_rows = None
    feature_count = None
    try:
        df = pd.read_csv(DATASET_PATH)
        dataset_rows = int(len(df))
        feature_count = int(len(df.columns) - 1)  # exclude target column
    except Exception:
        pass

    return JSONResponse({
        "model_ready": model_ready,
        "trained_at": trained_at,
        "dataset_rows": dataset_rows,
        "feature_count": feature_count,
    })


@app.get("/train",tags=["pipeline"])
async def train_route():
    try:
        started = time.time()
        train_pipeline=TrainingPipeline()
        artifact = train_pipeline.run_pipeline()
        elapsed = round(time.time() - started, 2)

        return JSONResponse({
            "status": "success",
            "message": "Training pipeline completed successfully.",
            "elapsed_seconds": elapsed,
            "model_file_path": artifact.trained_model_file_path,
            "train_metrics": {
                "f1_score": float(artifact.trained_metric_artifact.f1_score),
                "precision_score": float(artifact.trained_metric_artifact.precision_score),
                "recall_score": float(artifact.trained_metric_artifact.recall_score),
            },
            "test_metrics": {
                "f1_score": float(artifact.test_metric_artifact.f1_score),
                "precision_score": float(artifact.test_metric_artifact.precision_score),
                "recall_score": float(artifact.test_metric_artifact.recall_score),
            },
        })
    except Exception as e:
        raise NetworkSecurityException(e,sys)


@app.post("/predict",tags=["pipeline"])
async def predict_route(request:Request,file:UploadFile=File(...)):
    try:
        batch_pipeline=BatchPipeline()
        df = batch_pipeline.run_prediciton(file)

        feature_columns = [c for c in df.columns if c != "predicted_columns"]
        # .tolist() on a numpy array yields native Python int/float, unlike
        # iterating pandas Series items (which stay numpy int64/float64 and
        # aren't JSON-serializable by Starlette's default encoder).
        feature_matrix = df[feature_columns].values.tolist()
        predictions = [int(p) for p in df["predicted_columns"].tolist()]

        rows = []
        phishing_count = 0
        legitimate_count = 0

        for features, pred in zip(feature_matrix, predictions):
            if pred == 1:
                legitimate_count += 1
            elif pred == -1:
                phishing_count += 1

            rows.append({
                "features": features,
                "prediction": pred,
                "verdict": VERDICT_LABELS.get(pred, "Unknown"),
            })

        return JSONResponse({
            "columns": feature_columns,
            "rows": rows,
            "summary": {
                "total": len(df),
                "phishing": phishing_count,
                "legitimate": legitimate_count,
            },
        })
    except Exception as e:
        raise NetworkSecurityException(e,sys)


if __name__=="__main__":
    app_run(app,host="0.0.0.0",port=8080)


import sys
from networksecurity.exception.exception import NetworkSecurityException



from networksecurity.utils.main_utils.utils import load_object
from networksecurity.utils.ml_utils.model.estimator import NetworkModel



import os
import pandas as pd

class BatchPipeline:

    def run_prediciton(self,file):
        """
        Runs batch prediction on an uploaded CSV and returns the scored
        DataFrame. Kept separate from any HTML/JSON rendering so this
        stays reusable regardless of what's calling it (API, script, etc).
        """
        try:
            df=pd.read_csv(file.file)
            preprocessor=load_object("final_model/preprocessor.pkl")
            final_model=load_object("final_model/model.pkl")
            
            network_model=NetworkModel(preprocessor=preprocessor,model=final_model)
            
            print(df.iloc[0])
            
            y_pred=network_model.predict(df)
            print(y_pred)
            df["predicted_columns"]=y_pred
            print(df["predicted_columns"])

            os.makedirs("prediction_output",exist_ok=True)
            df.to_csv("prediction_output/output.csv")
            return df
        except Exception as e:
            raise NetworkSecurityException(e,sys)

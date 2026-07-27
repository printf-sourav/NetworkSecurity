
import sys
from networksecurity.exception.exception import NetworkSecurityException



from networksecurity.utils.main_utils.utils import load_object
from networksecurity.utils.ml_utils.model.estimator import NetworkModel



import pandas as pd

class BatchPipeline:

    def run_prediciton(self,file):

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
            df.to_csv("prediction_output/output.csv")
            table_html = df.to_html(classes="table table-striped")
            return table_html
        except Exception as e:
            raise NetworkSecurityException(e,sys)

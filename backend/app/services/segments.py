from app.services.booking_data import get_booking_data_from_db
import pandas as pd
from app.services.get_models import get_pretrained_model
from app.config import SEG_CAT_COLUMNS, SEG_NUMERICAL_COLUMNS


def genrate_segments(email:str): 
    #Step 1: get saved cleaned booking data
    df_saved = get_booking_data_from_db(email)
    
    #Step 2: encode and scale the data
    df_final= data_encode_and_scale(df_saved)
    
    #Step 3: add sengents
    df_segmented = segment_customers(df_saved, df_final)
    
       
def data_encode_and_scale(df_saved:pd.DataFrame):
    df_numericals = df_saved[SEG_NUMERICAL_COLUMNS]
    df_categorical = df_saved[SEG_CAT_COLUMNS]

    df_encoded = encode_data(df_categorical)
    df_scaled = scale_data(df_numericals)
    
    #Step 4: join scaled numerical and encoded categorical columns
    df_final= pd.concat([df_scaled,df_encoded ], axis=1)
    
    return df_final
        
        
def encode_data(df_cat:pd.DataFrame):
    {model} = get_pretrained_model("scaler.pkl")
    # data encoding 
    
def scale_data(df_cat:pd.DataFrame):
    {model} = get_pretrained_model("encoder.pkl")
    # data scalling 

def segment_customers (df_saved: pd.DataFrame, df_final: pd.DataFrame): 
     {model} = get_pretrained_model("kmeans.pkl")
    # data encoding 
from app.services.booking_data import get_booking_data_from_db,insert_segment_records
from app.services.get_models import get_pretrained_model
from app.config import SEG_CAT_COLUMNS, SEG_NUMERICAL_COLUMNS, AMENITY_COLUMNS
import pandas as pd
from app.db.supabase_client import supabase
import time
import joblib   
from io import BytesIO


def generate_segments(email: str): 
    df_saved = get_booking_data_from_db(email)
    if df_saved.empty:
        return {"success": False, "message": "No booking data found for this user."}
    df_final = data_encode_and_scale(df_saved)
    df_segmented = segment_customers(df_saved, df_final)
    response = insert_segment_records(df_segmented)
    return response


def data_encode_and_scale(df_saved: pd.DataFrame) -> pd.DataFrame:
    df_numericals = df_saved[SEG_NUMERICAL_COLUMNS + AMENITY_COLUMNS]
    df_categorical = df_saved[SEG_CAT_COLUMNS]

    df_encoded = encode_data(df_categorical)
    df_final = pd.concat([df_encoded,df_numericals ], axis=1)
    df_scaled = scale_data(df_final)

    return df_scaled


def encode_data(df_cat: pd.DataFrame):
    result = get_pretrained_model("encoder.pkl")
    encoder = result.get("model")

    if encoder is None:
        raise ValueError("Encoder not loaded")
    
    encoded_array = encoder.transform(df_cat)
    
    feature_names = encoder.get_feature_names_out(df_cat.columns)

    return pd.DataFrame(encoded_array, columns= feature_names, index=df_cat.index)


def scale_data(df_num: pd.DataFrame):
    print(df_num.info())
    result = get_pretrained_model("scaler.pkl")
    scaler = result.get("model")
    expected_n_features = scaler.mean_.shape[0]
    print("Scaler expects this many features:", expected_n_features)
    if scaler is None:
        raise ValueError("Scaler not loaded")

    return pd.DataFrame(scaler.transform(df_num), columns=df_num.columns,  index=df_num.index)


def segment_customers(df_saved: pd.DataFrame, df_final: pd.DataFrame):
    # Load PCA model
    result_pca = get_pretrained_model("pca.pkl")
    if not result_pca.get("success"):
        raise ValueError(f"PCA model not loaded: {result_pca.get('message')}")

    pca = result_pca["model"]

    # Apply PCA to input features
    X_pca = pca.transform(df_final)

    # Load GMM model
    result_gmm = get_pretrained_model("gmm.pkl")
    if not result_gmm.get("success"):
        raise ValueError(f"GMM model not loaded: {result_gmm.get('message')}")

    gmm = result_gmm["model"]
    model_version = result_gmm["model_version"]

    # Predict clusters using GMM
    start_time = time.time()
    df_saved["segment_cluster"] = gmm.predict(X_pca)
    duration = time.time() - start_time

    # Log cluster summary
    log_kmeans_details(gmm, X_pca, duration, feature_names=[f"PC{i+1}" for i in range(X_pca.shape[1])])

    # Save model version
    df_saved["model_version"] = model_version

    return df_saved

def log_kmeans_details(model, X_scaled, duration, feature_names=None, show_labels_sample=True):
    """
    Logs key details about a trained clustering model (KMeans or GMM).
    """
    print("\n📊 === Clustering Model Summary ===\n")

    # GMM does not use inertia, so we handle both models generically
    if hasattr(model, 'n_clusters'):
        print(f"🔹 Number of clusters (KMeans): {model.n_clusters}")
        print(f"🔹 Inertia: {getattr(model, 'inertia_', 'N/A')}")
    elif hasattr(model, 'n_components'):
        print(f"🔹 Number of clusters (GMM): {model.n_components}")
        print(f"🔹 Converged: {model.converged_}")
        print(f"🔹 Log-likelihood: {model.lower_bound_:.2f}")
        print(f"🔹 Iterations: {model.n_iter_}")
    
    print(f"⏱️ Prediction time for {len(X_scaled)} records: {duration:.4f} seconds")

    if feature_names is None:
        feature_names = [f"feature_{i}" for i in range(X_scaled.shape[1])]

    try:
        if hasattr(model, "means_"):
            centers_df = pd.DataFrame(model.means_, columns=feature_names)
            print("\n🏁 Cluster Centers (Means of Gaussian Components):\n")
            print(centers_df.to_string(index=True, float_format="%.2f"))
    except Exception as e:
        print(f"⚠️ Failed to print centers: {e}")

    if show_labels_sample:
        labels = model.predict(X_scaled)
        print(f"\n🔖 Sample Cluster Labels: {labels[:10]} ... (total {len(labels)})")

    print("\n✅ Clustering summary logging complete.\n")
    
    
def get_latest_segment_profiles(email):
    try:
        response = supabase.table("segment_profiles").select('*').eq("is_active", True).execute()
        if response.data:
            return {"success": True, "data": response.data}
        else:
            return {"success": False, "message": "unable to fetch segment profiles"}
        
    except Exception as e:
        return {"sucess": False, "message": f"something went wrong, {str(e)}"}
        
        
    
    
    
    
    
    
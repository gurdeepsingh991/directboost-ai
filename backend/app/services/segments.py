from app.services.booking_data import get_booking_data_from_db,insert_segment_records
from app.services.get_models import get_pretrained_model
from app.config import SEG_CAT_COLUMNS, SEG_NUMERICAL_COLUMNS
import pandas as pd
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

    return df_segmented


def data_encode_and_scale(df_saved: pd.DataFrame) -> pd.DataFrame:
    df_numericals = df_saved[SEG_NUMERICAL_COLUMNS]
    df_categorical = df_saved[SEG_CAT_COLUMNS]

    df_encoded = encode_data(df_categorical)
    df_scaled = scale_data(df_numericals)

    df_final = pd.concat([df_scaled, df_encoded], axis=1)
    return df_final


def encode_data(df_cat: pd.DataFrame):
    result = get_pretrained_model("encoder.pkl")
    encoder = result.get("model")

    if encoder is None:
        raise ValueError("Encoder not loaded")
    
    encoded_array = encoder.transform(df_cat)
    
    feature_names = encoder.get_feature_names_out(df_cat.columns)

    return pd.DataFrame(encoded_array, columns= feature_names, index=df_cat.index)


def scale_data(df_num: pd.DataFrame):
    result = get_pretrained_model("scaler.pkl")
    scaler = result.get("model")

    if scaler is None:
        raise ValueError("Scaler not loaded")

    return pd.DataFrame(scaler.transform(df_num), columns=df_num.columns,  index=df_num.index)


def segment_customers(df_saved: pd.DataFrame, df_final: pd.DataFrame):
    result = get_pretrained_model("kmeans.pkl")

    if not result.get("success"):
        raise ValueError("Segmentation model not loaded")

    kmeans = result["model"]
    model_version = result["model_version"]

    start_time = time.time()
    df_saved["segment_cluster"] = kmeans.predict(df_final)
    duration = time.time() - start_time

    log_kmeans_details(kmeans, df_final, duration, feature_names=df_final.columns.tolist())

    # Save model version with output
    df_saved["model_version"] = model_version

    return df_saved

def log_kmeans_details(model, X_scaled,duration, feature_names=None, show_labels_sample=True):
    """
    Logs key details about a trained KMeans model.
    
    Args:
        model: Trained sklearn.cluster.KMeans instance
        X_scaled: The scaled feature data (2D array or DataFrame)
        feature_names: List of column names (optional but recommended)
        show_labels_sample: Whether to print a few predicted labels (default: True)
    """
    print("\n📊 === KMeans Model Summary ===\n")
    
    # Number of clusters
    print(f"🔹 Number of clusters (k): {model.n_clusters}")
    
    # Inertia
    print(f"🔹 Inertia (sum of squared distances): {model.inertia_:.2f}")
    
    # Number of iterations
    print(f"🔹 Converged in iterations: {model.n_iter_}")
    
    # Time taken (if available — needs to be measured externally)
    if hasattr(model, "_fit_time"):
        print(f"⏱️ Time taken to train: {model._fit_time:.4f} seconds")
        
    print(f"⏱️ Prediction time for {len(X_scaled)} records: {duration:.4f} seconds\n")

    # Cluster centers
    print("\n🏁 Cluster Centers (Feature Means per Cluster):\n")
    if feature_names is None:
        feature_names = [f"feature_{i}" for i in range(X_scaled.shape[1])]

    centers_df = pd.DataFrame(model.cluster_centers_, columns=feature_names)
    print(centers_df.to_string(index=True, float_format="%.2f"))
    
    # Labels (Optional)
    if show_labels_sample:
        labels = model.labels_ if hasattr(model, "labels_") else model.predict(X_scaled)
        print(f"\n🔖 Sample Cluster Labels: {labels[:10]} ... (total {len(labels)})")

    print("\n✅ KMeans logging complete.\n")
    
    
    
    
    
    
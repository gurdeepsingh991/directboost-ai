
from app.services.data_cleanup import clean_booking_data

df_cleaned = clean_booking_data("data/your_file.csv")
print(df_cleaned.head())
print(f"Rows: {len(df_cleaned)} | Columns: {df_cleaned.columns.tolist()}")
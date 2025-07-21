
from app.services.data_cleanup import clean_booking_data

df_cleaned = clean_booking_data("data/booking data.xlsx")
print(df_cleaned.head())
print(f"Rows: {len(df_cleaned)} | Columns: {df_cleaned.columns.tolist()}")

# Save to Excel in the same folder
df_cleaned.to_csv("data/cleaned_booking_data.csv", index=False)
print("Cleaned data saved to: data/cleaned_booking_data.csv")
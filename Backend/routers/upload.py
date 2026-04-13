

from fastapi import APIRouter, UploadFile, File, HTTPException
from utils.ml_engine import process_uploaded_csv

router = APIRouter()


@router.post("/upload")
async def upload_sales_data(file: UploadFile = File(...)):

    # Only accept CSV files
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    content = await file.read()

    try:
        df = process_uploaded_csv(content)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")

    # Return a summary of what was uploaded
    return {
        "status":       "success",
        "filename":     file.filename,
        "total_months": len(df),
        "date_range": {
            "from": str(df["YearMonth_dt"].min())[:10],
            "to":   str(df["YearMonth_dt"].max())[:10],
        },
        "total_sales":  round(float(df["Total_Sales"].sum()), 2),
        "avg_monthly":  round(float(df["Total_Sales"].mean()), 2),
        "monthly_data": [
            {"month": str(row["YearMonth_dt"])[:7], "sales": round(row["Total_Sales"], 2)}
            for _, row in df.iterrows()
        ]
    }

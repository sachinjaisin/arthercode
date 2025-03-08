from fastapi import APIRouter, Depends, HTTPException,File,Query
from sqlalchemy.orm import Session
from models import StockPrice
from schemas import *
from database import SessionLocal
import io
import pandas as pd
from datetime import date
from sqlalchemy import or_
router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
 


@router.post("/upload-csv/")  
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        contents = await file.read()

        # Read CSV without headers (we will manually define them)
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")), header=None)

        # Extract Ticker Name from the second row
        ticker = df.iloc[1, 1]  # Correctly extract "RELIANCE.NS"

        # Drop first three rows (Price row + Ticker row + NaN row)
        df = df.iloc[3:].reset_index(drop=True)

        # Rename columns correctly based on known structure
        df.columns = ["date", "close", "high", "low", "open", "volume"]

        # Convert 'date' column from MM/DD/YYYY to YYYY-MM-DD
        df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce").dt.date  

        # Convert numeric fields
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df["high"] = pd.to_numeric(df["high"], errors="coerce")
        df["low"] = pd.to_numeric(df["low"], errors="coerce")
        df["open"] = pd.to_numeric(df["open"], errors="coerce")
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce", downcast="integer")

        # Drop rows with NaN values (avoids SQL errors)
        df = df.dropna()

        if df.empty:
            return {"message": "No valid records found in CSV", "total_records": 0}

        # Add ticker column to all rows
        df["ticker"] = ticker

        # Convert DataFrame to list of dictionaries
        records = df.to_dict(orient="records")

        # Bulk Insert into Database
        db.bulk_insert_mappings(StockPrice, records)
        db.commit()

        return {"message": "Data inserted successfully", "total_records": len(records)}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")
    

@router.get("/stocks")
def get_all_stocks(
    db: Session = Depends(get_db),
    ticker: Optional[str] = None,
    stock_date: Optional[date] = None,
    date_range: Optional[str] = None,
    low_range: Optional[str] = None,
    high_range: Optional[str] = None,
    volume_range: Optional[str] = None,
    page: int = Query(1, alias="page", ge=1),
    page_size: int = Query(10, alias="page_size", ge=1, le=100),
):
    query = db.query(StockPrice)

    if ticker:
        query = query.filter(
            or_(
                StockPrice.ticker.ilike(f"%{ticker}%"),
                StockPrice.ticker.ilike(f"%{ticker.replace('.NS', '')}%")
            )
        )

    if stock_date:
        query = query.filter(StockPrice.date == stock_date)

    if date_range:
        try:
            min_date_str, max_date_str = date_range.split(",")
            min_date = date.fromisoformat(min_date_str.strip())
            max_date = date.fromisoformat(max_date_str.strip())
            query = query.filter(StockPrice.date.between(min_date, max_date))
        except ValueError:
            return {"status": "error", "message": "Invalid date_range format. Use YYYY-MM-DD,YYYY-MM-DD.", "data": None}

    if low_range:
        try:
            min_low, max_low = map(float, low_range.split(","))
            query = query.filter(StockPrice.low.between(min_low, max_low))
        except ValueError:
            return {"status": "error", "message": "Invalid low_range format. Use min,max.", "data": None}

    if high_range:
        try:
            min_high, max_high = map(float, high_range.split(","))
            query = query.filter(StockPrice.high.between(min_high, max_high))
        except ValueError:
            return {"status": "error", "message": "Invalid high_range format. Use min,max.", "data": None}

    if volume_range:
        try:
            min_volume, max_volume = map(int, volume_range.split(","))
            query = query.filter(StockPrice.volume.between(min_volume, max_volume))
        except ValueError:
            return {"status": "error", "message": "Invalid volume_range format. Use min,max.", "data": None}

    total_records = query.count()
    offset = (page - 1) * page_size
    stocks = query.offset(offset).limit(page_size).all()

    results = [
        {
            "id": str(stock.id),
            "date": stock.date.isoformat() if stock.date else None,
            "close": stock.close,
            "high": stock.high,
            "low": stock.low,
            "open": stock.open,
            "volume": stock.volume,
            "ticker": stock.ticker
        }
        for stock in stocks
    ]

    return {
        "status": "success",
        "message": "Stock prices retrieved successfully",
        "data": results,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_records": total_records,
            "total_pages": (total_records // page_size) + (1 if total_records % page_size else 0)
        }
    }

import os

import pandas as pd
from sqlalchemy import text

from app.database import engine


EXPORT_FOLDER = "exports"

os.makedirs(EXPORT_FOLDER, exist_ok=True)


class ExportService:

    @staticmethod
    def export_top10_high():

        query = text("""
            SELECT
                trading_symbol,
                exchange,
                token,
                ltp,
                volume,
                exchange_time
            FROM backtest_data
            WHERE trading_symbol IS NOT NULL
              AND ltp IS NOT NULL
        """)

        df = pd.read_sql(query, engine)

        if df.empty:
            return None

        df["exchange_time"] = pd.to_datetime(df["exchange_time"])

        latest_date = df["exchange_time"].dt.date.max()

        df = df[df["exchange_time"].dt.date == latest_date]

        result = (
            df
            .sort_values(
                ["trading_symbol", "ltp"],
                ascending=[True, False]
            )
            .groupby("trading_symbol", group_keys=False)
            .head(10)
        )

        file_name = f"top10_high_{latest_date}.csv"

        file_path = os.path.join(
            EXPORT_FOLDER,
            file_name
        )

        result.to_csv(
            file_path,
            index=False
        )

        return file_path
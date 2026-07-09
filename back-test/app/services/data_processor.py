import pandas as pd
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self):
        self.required_columns = [
            'user_id', 'exchange', 'token', 'trading_symbol',
            'instrument_type', 'ltp', 'volume', 'open_interest', 'bid_ask'
        ]
    
    def process_csv(self, df: pd.DataFrame) -> pd.DataFrame:
        try:
            logger.info(f"Processing {len(df)} rows")
            df = self._clean_data(df)
            df = self._validate_columns(df)
            df = self._add_metadata(df)
            df = self._convert_types(df)
            logger.info(f"Successfully processed {len(df)} rows")
            return df
        except Exception as e:
            logger.error(f"Error processing data: {e}")
            raise

    def _clean_data(self, df):
        df = df.drop_duplicates()
        df = df.fillna({
            'user_id': 'unknown',
            'exchange': 'NSE',
            'token': '0',
            'trading_symbol': 'UNKNOWN',
            'instrument_type': 'EQ',
            'ltp': 0.0,
            'volume': 0,
            'open_interest': 0,
            'bid_ask': 0
        })
        df = df[df['trading_symbol'].notna()]
        df = df[df['trading_symbol'] != '']
        df = df[df['trading_symbol'] != 'UNKNOWN']
        str_cols = df.select_dtypes(include=['object']).columns
        for col in str_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        return df

    def _validate_columns(self, df):
        df.columns = df.columns.str.lower().str.replace(' ', '_')
        missing = set(self.required_columns) - set(df.columns)
        for col in missing:
            alt = [col, col.upper(), col.title(), col.replace('_', ' ')]
            found = False
            for a in alt:
                if a in df.columns:
                    df.rename(columns={a: col}, inplace=True)
                    found = True
                    break
            if not found:
                logger.warning(f"Column '{col}' not found, adding default")
                df[col] = None
        needed = self.required_columns + ['date', 'timestamp']
        existing = [c for c in needed if c in df.columns]
        return df[existing]

    def _convert_types(self, df):
        for col in ['ltp', 'volume', 'open_interest', 'bid_ask']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        for col in ['user_id', 'exchange', 'token', 'trading_symbol', 'instrument_type']:
            if col in df.columns:
                df[col] = df[col].astype(str)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        return df

    def _add_metadata(self, df):
        if 'timestamp' not in df.columns:
            df['timestamp'] = datetime.now()
        if 'date' not in df.columns:
            df['date'] = datetime.now()
        return df
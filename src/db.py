"""データベース管理モジュール"""
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict
import pandas as pd
from src.config import DB_PATH
import os


def get_connection():
    """データベース接続を取得"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    return conn


def init_database():
    """データベースを初期化"""
    conn = get_connection()
    cursor = conn.cursor()

    # market_pricesテーブル
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS market_prices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        datetime TEXT NOT NULL,
        date TEXT NOT NULL,
        slot INTEGER NOT NULL,
        area TEXT NOT NULL,
        system_price_yen_per_kwh REAL,
        area_price_yen_per_kwh REAL,
        source_url TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # area_generationテーブル
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS area_generation (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        datetime TEXT NOT NULL,
        date TEXT NOT NULL,
        slot INTEGER NOT NULL,
        area TEXT NOT NULL,
        source_type TEXT NOT NULL,
        generation_kw_avg REAL,
        generation_kwh REAL,
        source_url TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # pv_profilesテーブル
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pv_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plant_name TEXT NOT NULL,
        datetime TEXT NOT NULL,
        generation_kwh REAL NOT NULL,
        generation_type TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # simulation_resultsテーブル
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS simulation_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        simulation_name TEXT NOT NULL,
        datetime TEXT NOT NULL,
        area TEXT NOT NULL,
        market_price_yen_per_kwh REAL,
        pv_generation_kwh REAL,
        battery_charge_kwh REAL,
        battery_discharge_kwh REAL,
        battery_soc_kwh REAL,
        export_kwh REAL,
        revenue_yen REAL
    )
    """)

    conn.commit()
    conn.close()


def save_market_prices(df: pd.DataFrame):
    """市場価格データを保存"""
    conn = get_connection()
    df.to_sql('market_prices', conn, if_exists='append', index=False)
    conn.close()


def save_area_generation(df: pd.DataFrame):
    """エリア発電実績データを保存"""
    conn = get_connection()
    df.to_sql('area_generation', conn, if_exists='append', index=False)
    conn.close()


def save_pv_profile(plant_name: str, df: pd.DataFrame):
    """太陽光発電プロファイルを保存"""
    conn = get_connection()
    df['plant_name'] = plant_name
    df['created_at'] = datetime.now().isoformat()
    df.to_sql('pv_profiles', conn, if_exists='append', index=False)
    conn.close()


def save_simulation_results(simulation_name: str, df: pd.DataFrame):
    """シミュレーション結果を保存"""
    conn = get_connection()
    df['simulation_name'] = simulation_name
    df.to_sql('simulation_results', conn, if_exists='append', index=False)
    conn.close()


def get_market_prices(area: str, start_date: str, end_date: str) -> pd.DataFrame:
    """市場価格データを取得"""
    conn = get_connection()
    query = """
    SELECT datetime, area, area_price_yen_per_kwh, system_price_yen_per_kwh
    FROM market_prices
    WHERE area = ? AND date BETWEEN ? AND ?
    ORDER BY datetime
    """
    df = pd.read_sql_query(query, conn, params=(area, start_date, end_date))
    conn.close()
    return df


def get_area_generation(area: str, source_type: str, start_date: str, end_date: str) -> pd.DataFrame:
    """エリア発電実績データを取得"""
    conn = get_connection()
    query = """
    SELECT datetime, area, source_type, generation_kwh
    FROM area_generation
    WHERE area = ? AND source_type = ? AND date BETWEEN ? AND ?
    ORDER BY datetime
    """
    df = pd.read_sql_query(query, conn, params=(area, source_type, start_date, end_date))
    conn.close()
    return df


def get_pv_profile(plant_name: str) -> pd.DataFrame:
    """太陽光発電プロファイルを取得"""
    conn = get_connection()
    query = """
    SELECT datetime, generation_kwh
    FROM pv_profiles
    WHERE plant_name = ?
    ORDER BY datetime
    """
    df = pd.read_sql_query(query, conn, params=(plant_name,))
    conn.close()
    return df


def get_simulation_results(simulation_name: str) -> pd.DataFrame:
    """シミュレーション結果を取得"""
    conn = get_connection()
    query = """
    SELECT *
    FROM simulation_results
    WHERE simulation_name = ?
    ORDER BY datetime
    """
    df = pd.read_sql_query(query, conn, params=(simulation_name,))
    conn.close()
    return df


def list_pv_profiles() -> List[str]:
    """登録済みの太陽光発電所リストを取得"""
    conn = get_connection()
    query = "SELECT DISTINCT plant_name FROM pv_profiles"
    cursor = conn.cursor()
    cursor.execute(query)
    plants = [row[0] for row in cursor.fetchall()]
    conn.close()
    return plants


def check_data_availability(area: str, start_date: str, end_date: str) -> Dict[str, bool]:
    """データの利用可能性をチェック"""
    conn = get_connection()
    cursor = conn.cursor()

    # 市場価格データのチェック
    cursor.execute("""
    SELECT COUNT(*) FROM market_prices
    WHERE area = ? AND date BETWEEN ? AND ?
    """, (area, start_date, end_date))
    has_prices = cursor.fetchone()[0] > 0

    # エリア発電実績データのチェック
    cursor.execute("""
    SELECT COUNT(*) FROM area_generation
    WHERE area = ? AND date BETWEEN ? AND ?
    """, (area, start_date, end_date))
    has_generation = cursor.fetchone()[0] > 0

    conn.close()

    return {
        'market_prices': has_prices,
        'area_generation': has_generation
    }

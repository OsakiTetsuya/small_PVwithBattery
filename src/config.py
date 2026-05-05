"""設定ファイル"""
import os

# データベースパス
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "app.db")
RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, "data", "processed")

# JEPXエリアリスト
JEPX_AREAS = [
    "北海道", "東北", "東京", "中部", "北陸",
    "関西", "中国", "四国", "九州"
]

# 電源種別リスト
SOURCE_TYPES = [
    "太陽光", "風力", "水力", "火力LNG", "火力石炭",
    "火力石油", "バイオマス", "原子力", "地熱",
    "揚水", "蓄電池", "連系線", "その他"
]

# デフォルト蓄電池設定
DEFAULT_BATTERY_CONFIG = {
    "battery_capacity_kwh": 50.0,
    "max_charge_kw": 25.0,
    "max_discharge_kw": 25.0,
    "charge_efficiency": 0.95,
    "discharge_efficiency": 0.95,
    "initial_soc_percent": 50.0,
    "min_soc_percent": 10.0,
    "max_soc_percent": 90.0,
    "pcs_capacity_kw": 50.0,
    "grid_export_limit_kw": 50.0,
    "operation_mode": "price_optimized"
}

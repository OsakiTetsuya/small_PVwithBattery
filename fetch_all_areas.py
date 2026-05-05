"""
全エリアデータ取得スクリプト

全9エリア（北海道、東北、東京、中部、北陸、関西、中国、四国、九州）の
エリア発電実績データとJEPX市場価格データを生成してデータベースに保存します。
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from datetime import datetime, timedelta
from src.db import init_database, save_area_generation, save_market_prices
from src.config import JEPX_AREAS
import random

# エリアごとの特性係数
AREA_CHARACTERISTICS = {
    "北海道": {
        "solar_factor": 0.8,   # 太陽光は控えめ（寒冷地）
        "wind_factor": 1.5,    # 風力が強い
        "hydro_factor": 1.2,   # 水力も多め
        "thermal_factor": 1.3, # 火力も多め（暖房需要）
        "price_offset": 0.5,   # 価格はやや高め
    },
    "東北": {
        "solar_factor": 0.9,
        "wind_factor": 1.2,
        "hydro_factor": 1.3,
        "thermal_factor": 1.1,
        "price_offset": 0.3,
    },
    "東京": {
        "solar_factor": 1.0,   # 基準
        "wind_factor": 0.7,
        "hydro_factor": 0.8,
        "thermal_factor": 1.5,
        "price_offset": 0.0,   # 基準価格
    },
    "中部": {
        "solar_factor": 1.1,
        "wind_factor": 0.8,
        "hydro_factor": 1.1,
        "thermal_factor": 1.2,
        "price_offset": -0.2,
    },
    "北陸": {
        "solar_factor": 0.85,
        "wind_factor": 0.9,
        "hydro_factor": 1.5,   # 水力が豊富
        "thermal_factor": 1.0,
        "price_offset": -0.3,
    },
    "関西": {
        "solar_factor": 1.05,
        "wind_factor": 0.75,
        "hydro_factor": 0.9,
        "thermal_factor": 1.4,
        "price_offset": -0.1,
    },
    "中国": {
        "solar_factor": 1.08,
        "wind_factor": 0.8,
        "hydro_factor": 1.0,
        "thermal_factor": 1.1,
        "price_offset": -0.15,
    },
    "四国": {
        "solar_factor": 1.12,  # 日照良好
        "wind_factor": 0.85,
        "hydro_factor": 1.1,
        "thermal_factor": 0.9,
        "price_offset": -0.25,
    },
    "九州": {
        "solar_factor": 1.15,  # 日照最良
        "wind_factor": 1.0,
        "hydro_factor": 1.0,
        "thermal_factor": 0.95,
        "price_offset": -0.4,  # 価格は比較的安め
    },
}


def generate_area_generation_data(area: str, date: str, weather_factor: float = 1.0) -> pd.DataFrame:
    """
    エリア発電実績データを生成（エリア特性を反映）

    Parameters:
    -----------
    area : str
        エリア名
    date : str
        対象日（YYYY-MM-DD形式）
    weather_factor : float
        天候係数（0.5～1.5、デフォルト1.0）

    Returns:
    --------
    pd.DataFrame
        サンプルデータ
    """
    characteristics = AREA_CHARACTERISTICS.get(area, AREA_CHARACTERISTICS["東京"])

    data = []
    base_date = datetime.strptime(date, '%Y-%m-%d')

    for slot in range(48):
        hour = slot // 2
        minute = (slot % 2) * 30
        dt = base_date + timedelta(hours=hour, minutes=minute)
        dt_str = dt.strftime('%Y-%m-%d %H:%M')

        # 太陽光発電量（昼間に多く、夜間はゼロ）
        if 6 <= hour <= 18:
            solar_base = 1000 + (hour - 6) * 500
            if hour > 12:
                solar_base = 1000 + (18 - hour) * 500
            solar_kw = max(0, solar_base * characteristics["solar_factor"] * weather_factor + random.randint(-100, 100))
        else:
            solar_kw = 0

        # 風力発電量（時間帯による変動）
        wind_base = 300 + (slot % 5) * 50
        wind_kw = max(0, wind_base * characteristics["wind_factor"] + random.randint(-50, 50))

        # 水力発電量（比較的安定）
        hydro_base = 500 + (slot % 4) * 100
        hydro_kw = max(0, hydro_base * characteristics["hydro_factor"] + random.randint(-30, 30))

        # 火力発電量（需要に応じて変動）
        thermal_base = 2000 + (hour % 8) * 200
        if 8 <= hour <= 20:  # 日中は需要増
            thermal_base *= 1.3
        thermal_kw = max(0, thermal_base * characteristics["thermal_factor"] + random.randint(-100, 100))

        sources = {
            '太陽光': solar_kw,
            '風力': wind_kw,
            '水力': hydro_kw,
            '火力': thermal_kw,
        }

        for source_type, kw_avg in sources.items():
            kwh = kw_avg * 0.5  # 30分なので0.5倍

            data.append({
                'datetime': dt_str,
                'date': date,
                'slot': slot,
                'area': area,
                'source_type': source_type,
                'generation_kw_avg': kw_avg,
                'generation_kwh': kwh,
                'source_url': 'sample_data_all_areas',
                'created_at': datetime.now().isoformat()
            })

    return pd.DataFrame(data)


def generate_market_prices(area: str, date: str, demand_factor: float = 1.0) -> pd.DataFrame:
    """
    JEPX市場価格データを生成（エリア特性を反映）

    Parameters:
    -----------
    area : str
        エリア名
    date : str
        対象日（YYYY-MM-DD形式）
    demand_factor : float
        需要係数（0.8～1.2、デフォルト1.0）

    Returns:
    --------
    pd.DataFrame
        サンプルデータ
    """
    characteristics = AREA_CHARACTERISTICS.get(area, AREA_CHARACTERISTICS["東京"])

    data = []
    base_date = datetime.strptime(date, '%Y-%m-%d')

    for slot in range(48):
        hour = slot // 2
        minute = (slot % 2) * 30
        dt = base_date + timedelta(hours=hour, minutes=minute)
        dt_str = dt.strftime('%Y-%m-%d %H:%M')

        # 時間帯に応じた基本価格
        if 7 <= hour <= 9:  # 朝のピーク
            base_price = 12.0 + (hour - 7) * 2
        elif 17 <= hour <= 20:  # 夕方のピーク
            base_price = 15.0 + (hour - 17) * 3
        elif 0 <= hour <= 5:  # 深夜は安い
            base_price = 6.0 + hour * 0.5
        else:
            base_price = 10.0 + (slot % 4) * 0.5

        # エリア特性と需要係数を反映
        area_price = (base_price + characteristics["price_offset"]) * demand_factor
        area_price = max(4.0, area_price)  # 最低価格

        # ランダムな変動を追加
        area_price += random.uniform(-0.5, 0.5)

        data.append({
            'datetime': dt_str,
            'date': date,
            'slot': slot,
            'area': area,
            'system_price_yen_per_kwh': area_price * 1.05,  # システムプライスは少し高め
            'area_price_yen_per_kwh': round(area_price, 2),
            'source_url': 'sample_data_all_areas',
            'created_at': datetime.now().isoformat()
        })

    return pd.DataFrame(data)


def main():
    """メイン処理"""
    print("\n" + "="*70)
    print("全エリアデータ取得スクリプト")
    print("全9エリア×3日分のデータを生成します")
    print("="*70)

    # データベース初期化
    print("\n1. データベース初期化中...")
    init_database()
    print("✓ データベース初期化完了")

    # 対象日
    dates = ["2025-07-01", "2025-07-02", "2025-07-03"]

    # 日ごとの天候・需要係数（ランダム）
    weather_factors = {
        "2025-07-01": 1.0,   # 晴天
        "2025-07-02": 0.85,  # 曇り
        "2025-07-03": 1.1,   # 快晴
    }

    demand_factors = {
        "2025-07-01": 1.0,
        "2025-07-02": 1.05,  # 需要やや高
        "2025-07-03": 0.95,  # 需要やや低
    }

    # 全エリアのデータを生成
    print(f"\n2. エリア発電実績データ生成中（全{len(JEPX_AREAS)}エリア）...")
    print("-" * 70)

    total_generation_records = 0
    for area in JEPX_AREAS:
        print(f"\n[{area}エリア]")
        area_records = 0

        for date in dates:
            weather_factor = weather_factors[date]
            df = generate_area_generation_data(area, date, weather_factor)

            try:
                save_area_generation(df)
                area_records += len(df)
                print(f"  ✓ {date}: {len(df)}件保存")
            except Exception as e:
                print(f"  ✗ {date}: エラー - {str(e)}")

        print(f"  小計: {area_records}件")
        total_generation_records += area_records

    print(f"\n✓ エリア発電実績データ合計: {total_generation_records}件")

    # 全エリアの市場価格を生成
    print(f"\n3. JEPX市場価格データ生成中（全{len(JEPX_AREAS)}エリア）...")
    print("-" * 70)

    total_price_records = 0
    for area in JEPX_AREAS:
        print(f"\n[{area}エリア]")
        area_records = 0

        for date in dates:
            demand_factor = demand_factors[date]
            df = generate_market_prices(area, date, demand_factor)

            try:
                save_market_prices(df)
                area_records += len(df)
                print(f"  ✓ {date}: {len(df)}件保存")
            except Exception as e:
                print(f"  ✗ {date}: エラー - {str(e)}")

        print(f"  小計: {area_records}件")
        total_price_records += area_records

    print(f"\n✓ JEPX市場価格データ合計: {total_price_records}件")

    # 統計表示
    print("\n" + "="*70)
    print("データ取得完了！")
    print("="*70)
    print(f"対象エリア: 全{len(JEPX_AREAS)}エリア")
    print(f"  - {', '.join(JEPX_AREAS)}")
    print(f"対象期間: {dates[0]} ～ {dates[-1]} ({len(dates)}日間)")
    print(f"\nエリア発電実績: {total_generation_records:,}件")
    print(f"JEPX市場価格: {total_price_records:,}件")
    print(f"合計: {total_generation_records + total_price_records:,}件")

    # エリアごとの統計
    print("\n" + "-"*70)
    print("エリア別データ件数:")
    print("-"*70)
    for area in JEPX_AREAS:
        gen_per_area = len(dates) * 48 * 4  # 3日×48コマ×4電源
        price_per_area = len(dates) * 48     # 3日×48コマ
        print(f"  {area:6s}: 発電実績 {gen_per_area:4d}件 + 市場価格 {price_per_area:3d}件 = {gen_per_area + price_per_area:4d}件")

    print("\n" + "="*70)
    print("次のステップ:")
    print("="*70)
    print("1. Streamlitアプリを起動: streamlit run app.py")
    print("2. 「データ取得」→「データ確認」で各エリアのデータを確認")
    print("3. 「発電所登録」で発電所データをアップロード")
    print("4. 「シミュレーション実行」で好きなエリアを選択してシミュレーション")
    print("5. 「結果分析」で結果を確認")
    print("\n💡 ヒント: 各エリアで価格や発電量の特性が異なります！")

    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nエラー: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

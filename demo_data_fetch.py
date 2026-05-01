"""
デモ用データ取得スクリプト

実際の環境ではネットワーク経由でデータを取得しますが、
このデモではサンプルデータを生成してデータベースに保存します。
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from datetime import datetime, timedelta
from src.db import init_database, save_area_generation, save_market_prices

def generate_sample_area_generation_data(area: str = "東京", date: str = "2025-07-01") -> pd.DataFrame:
    """
    サンプルのエリア発電実績データを生成

    Parameters:
    -----------
    area : str
        エリア名
    date : str
        対象日（YYYY-MM-DD形式）

    Returns:
    --------
    pd.DataFrame
        サンプルデータ
    """
    print(f"\n{'='*60}")
    print(f"サンプルエリア発電実績データ生成: {area}エリア {date}")
    print(f"{'='*60}")

    data = []

    # 30分単位のデータを生成（1日48コマ）
    base_date = datetime.strptime(date, '%Y-%m-%d')

    for slot in range(48):
        hour = slot // 2
        minute = (slot % 2) * 30
        dt = base_date + timedelta(hours=hour, minutes=minute)
        dt_str = dt.strftime('%Y-%m-%d %H:%M')

        # 時間帯に応じた太陽光発電量（昼間に多く、夜間はゼロ）
        if 6 <= hour <= 18:
            solar_base = 1000 + (hour - 6) * 500
            if hour > 12:
                solar_base = 1000 + (18 - hour) * 500
            solar_kw = max(0, solar_base + (slot % 3) * 200)
        else:
            solar_kw = 0

        # その他の電源（一定量）
        wind_kw = 300 + (slot % 5) * 50
        hydro_kw = 500 + (slot % 4) * 100
        thermal_kw = 2000 + (hour % 8) * 200

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
                'source_url': 'sample_data',
                'created_at': datetime.now().isoformat()
            })

    df = pd.DataFrame(data)
    print(f"✓ {len(df)}件のサンプルデータを生成しました")

    return df


def generate_sample_market_prices(area: str = "東京", date: str = "2025-07-01") -> pd.DataFrame:
    """
    サンプルのJEPX市場価格データを生成

    Parameters:
    -----------
    area : str
        エリア名
    date : str
        対象日（YYYY-MM-DD形式）

    Returns:
    --------
    pd.DataFrame
        サンプルデータ
    """
    print(f"\n{'='*60}")
    print(f"サンプルJEPX市場価格データ生成: {area}エリア {date}")
    print(f"{'='*60}")

    data = []

    # 30分単位のデータを生成（1日48コマ）
    base_date = datetime.strptime(date, '%Y-%m-%d')

    for slot in range(48):
        hour = slot // 2
        minute = (slot % 2) * 30
        dt = base_date + timedelta(hours=hour, minutes=minute)
        dt_str = dt.strftime('%Y-%m-%d %H:%M')

        # 時間帯に応じた価格設定
        if 7 <= hour <= 9:  # 朝のピーク
            price = 12.0 + (hour - 7) * 2
        elif 17 <= hour <= 20:  # 夕方のピーク
            price = 15.0 + (hour - 17) * 3
        elif 0 <= hour <= 5:  # 深夜は安い
            price = 6.0 + hour * 0.5
        else:
            price = 10.0 + (slot % 4)

        data.append({
            'datetime': dt_str,
            'date': date,
            'slot': slot,
            'area': area,
            'system_price_yen_per_kwh': price * 1.1,
            'area_price_yen_per_kwh': price,
            'source_url': 'sample_data',
            'created_at': datetime.now().isoformat()
        })

    df = pd.DataFrame(data)
    print(f"✓ {len(df)}件のサンプルデータを生成しました")

    return df


def main():
    """メイン処理"""
    print("\n" + "="*60)
    print("エリア発電実績データ取得デモ")
    print("="*60)

    # データベース初期化
    print("\n1. データベース初期化中...")
    init_database()
    print("✓ データベース初期化完了")

    # エリア発電実績データを生成
    print("\n2. エリア発電実績データ生成中...")
    areas = ["東京"]
    dates = ["2025-07-01", "2025-07-02", "2025-07-03"]

    total_records = 0
    for area in areas:
        for date in dates:
            df = generate_sample_area_generation_data(area, date)

            # データベースに保存
            try:
                save_area_generation(df)
                print(f"✓ データベースに保存: {area} {date} ({len(df)}件)")
                total_records += len(df)
            except Exception as e:
                print(f"✗ 保存エラー: {str(e)}")

    print(f"\n✓ エリア発電実績データ合計: {total_records}件")

    # JEPX市場価格データを生成
    print("\n3. JEPX市場価格データ生成中...")
    total_price_records = 0
    for area in areas:
        for date in dates:
            df = generate_sample_market_prices(area, date)

            # データベースに保存
            try:
                save_market_prices(df)
                print(f"✓ データベースに保存: {area} {date} ({len(df)}件)")
                total_price_records += len(df)
            except Exception as e:
                print(f"✗ 保存エラー: {str(e)}")

    print(f"\n✓ JEPX市場価格データ合計: {total_price_records}件")

    # 統計表示
    print("\n" + "="*60)
    print("データ取得完了")
    print("="*60)
    print(f"エリア発電実績: {total_records}件")
    print(f"JEPX市場価格: {total_price_records}件")
    print(f"合計: {total_records + total_price_records}件")

    print("\n次のステップ:")
    print("1. Streamlitアプリを起動: streamlit run app.py")
    print("2. 「発電所登録」ページで発電所データをアップロード")
    print("3. 「シミュレーション実行」ページでシミュレーション実行")
    print("4. 「結果分析」ページで結果を確認")

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

"""基本的な機能テスト"""
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from datetime import datetime, timedelta
from src import db, config, pv_profile, battery, revenue

def test_database():
    """データベース初期化テスト"""
    print("Testing database initialization...")
    db.init_database()
    print("✓ Database initialized successfully")

def test_pv_profile_conversion():
    """PVプロファイル変換テスト"""
    print("\nTesting PV profile conversion...")

    # テストデータ作成
    data = {
        'datetime': ['2025-07-01 10:00', '2025-07-01 11:00', '2025-07-01 12:00'],
        'generation_kwh': [20.0, 30.0, 35.0]
    }
    df = pd.DataFrame(data)

    # 1時間→30分変換
    df_30min = pv_profile.convert_hourly_to_30min(df)

    assert len(df_30min) == len(df) * 2, "変換後のデータ数が不正"
    assert df_30min['generation_kwh'].sum() == df['generation_kwh'].sum(), "総発電量が一致しない"

    print(f"✓ Converted {len(df)} hourly records to {len(df_30min)} 30-min records")

def test_battery_simulator():
    """蓄電池シミュレーターテスト"""
    print("\nTesting battery simulator...")

    # テストデータ（1日48スロット分）
    pv_gen = pd.Series([0] * 48, index=range(48))
    prices = pd.Series([10.0] * 48, index=range(48))

    # 日中の発電データを設定
    for i in range(12, 36):  # 6:00-18:00
        pv_gen[i] = 15.0

    # ピーク時間帯の価格を高く設定
    for i in range(36, 42):  # 18:00-21:00
        prices[i] = 20.0

    # 蓄電池設定
    battery_config = config.DEFAULT_BATTERY_CONFIG.copy()
    sim = battery.BatterySimulator(battery_config)

    # 放電スロットを決定（上位2スロット）
    discharge_slots = sim.determine_discharge_slots_top_price(prices, num_slots=2)

    # シミュレーション実行
    results = sim.simulate_day(pv_gen, prices, discharge_slots)

    assert len(results) == 48, f"結果の数が不正: expected 48, got {len(results)}"
    print(f"✓ Battery simulation completed with {len(discharge_slots)} discharge slots")

def test_revenue_calculation():
    """売上計算テスト"""
    print("\nTesting revenue calculation...")

    # テストデータ
    data = {
        'datetime': pd.date_range('2025-07-01', periods=48, freq='30min'),
        'pv_generation_kwh': [10.0] * 48,
        'export_kwh': [8.0] * 48,
        'revenue_yen': [100.0] * 48
    }
    df = pd.DataFrame(data)

    # 日別サマリー
    daily = revenue.calculate_daily_summary(df)

    assert len(daily) > 0, "日別サマリーが空"
    assert 'revenue_yen' in daily.columns, "売上列がない"

    print(f"✓ Revenue calculation completed: {len(daily)} days")

def run_all_tests():
    """全テストを実行"""
    print("=" * 50)
    print("Running Basic Functionality Tests")
    print("=" * 50)

    try:
        test_database()
        test_pv_profile_conversion()
        test_battery_simulator()
        test_revenue_calculation()

        print("\n" + "=" * 50)
        print("All tests passed! ✓")
        print("=" * 50)
        return True

    except Exception as e:
        print(f"\n✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

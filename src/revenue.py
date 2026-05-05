"""売上計算モジュール"""
import pandas as pd
from typing import Dict, Optional


def calculate_revenue_without_battery(
    pv_df: pd.DataFrame,
    prices_df: pd.DataFrame,
    grid_export_limit_kw: float,
    pcs_capacity_kw: float
) -> pd.DataFrame:
    """
    蓄電池なしの売上計算

    Parameters:
    -----------
    pv_df : pd.DataFrame
        columns: ['datetime', 'generation_kwh']
    prices_df : pd.DataFrame
        columns: ['datetime', 'area_price_yen_per_kwh']
    grid_export_limit_kw : float
        系統売電上限 [kW]
    pcs_capacity_kw : float
        PCS容量 [kW]

    Returns:
    --------
    pd.DataFrame
        columns: ['datetime', 'market_price_yen_per_kwh', 'pv_generation_kwh',
                  'export_kwh', 'revenue_yen']
    """
    # データをマージ
    df = pd.merge(pv_df, prices_df, on='datetime', how='inner')

    # 30分あたりの上限
    grid_limit_30min = grid_export_limit_kw * 0.5
    pcs_limit_30min = pcs_capacity_kw * 0.5

    # 売電量を計算
    df['export_kwh'] = df['generation_kwh'].clip(upper=grid_limit_30min)
    df['export_kwh'] = df['export_kwh'].clip(upper=pcs_limit_30min)
    df['export_kwh'] = df['export_kwh'].clip(lower=0)

    # 売上を計算
    df['revenue_yen'] = df['export_kwh'] * df['area_price_yen_per_kwh']

    return df[['datetime', 'market_price_yen_per_kwh', 'pv_generation_kwh',
               'export_kwh', 'revenue_yen']]


def calculate_revenue_summary(df: pd.DataFrame) -> Dict:
    """
    売上サマリーを計算

    Parameters:
    -----------
    df : pd.DataFrame
        シミュレーション結果データフレーム
        columns: ['datetime', 'revenue_yen', 'pv_generation_kwh', 'export_kwh']

    Returns:
    --------
    Dict
        売上サマリー
    """
    df = df.copy()
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['date'] = df['datetime'].dt.date
    df['month'] = df['datetime'].dt.to_period('M')
    df['hour'] = df['datetime'].dt.hour

    summary = {
        'total_revenue_yen': df['revenue_yen'].sum(),
        'total_generation_kwh': df['pv_generation_kwh'].sum(),
        'total_export_kwh': df['export_kwh'].sum(),
        'average_price_yen_per_kwh': df['revenue_yen'].sum() / df['export_kwh'].sum() if df['export_kwh'].sum() > 0 else 0,
        'daily_revenue': df.groupby('date')['revenue_yen'].sum().to_dict(),
        'monthly_revenue': df.groupby('month')['revenue_yen'].sum().to_dict(),
        'hourly_revenue': df.groupby('hour')['revenue_yen'].sum().to_dict(),
    }

    return summary


def compare_with_without_battery(
    results_with_battery: pd.DataFrame,
    results_without_battery: pd.DataFrame
) -> Dict:
    """
    蓄電池あり/なしの比較

    Parameters:
    -----------
    results_with_battery : pd.DataFrame
        蓄電池ありのシミュレーション結果
    results_without_battery : pd.DataFrame
        蓄電池なしのシミュレーション結果

    Returns:
    --------
    Dict
        比較結果
    """
    revenue_with = results_with_battery['revenue_yen'].sum()
    revenue_without = results_without_battery['revenue_yen'].sum()

    export_with = results_with_battery['export_kwh'].sum()
    export_without = results_without_battery['export_kwh'].sum()

    comparison = {
        'revenue_with_battery_yen': revenue_with,
        'revenue_without_battery_yen': revenue_without,
        'revenue_increase_yen': revenue_with - revenue_without,
        'revenue_increase_percent': (revenue_with - revenue_without) / revenue_without * 100 if revenue_without > 0 else 0,
        'export_with_battery_kwh': export_with,
        'export_without_battery_kwh': export_without,
        'export_increase_kwh': export_with - export_without,
    }

    return comparison


def calculate_daily_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    日別サマリーを計算

    Parameters:
    -----------
    df : pd.DataFrame
        シミュレーション結果データフレーム

    Returns:
    --------
    pd.DataFrame
        日別サマリー
    """
    df = df.copy()
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['date'] = df['datetime'].dt.date

    agg_dict = {
        'pv_generation_kwh': 'sum',
        'export_kwh': 'sum',
        'revenue_yen': 'sum',
    }

    if 'battery_charge_kwh' in df.columns:
        agg_dict['battery_charge_kwh'] = 'sum'
    if 'battery_discharge_kwh' in df.columns:
        agg_dict['battery_discharge_kwh'] = 'sum'

    daily = df.groupby('date').agg(agg_dict).reset_index()

    daily['average_price_yen_per_kwh'] = daily['revenue_yen'] / daily['export_kwh']

    return daily


def calculate_monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    月別サマリーを計算

    Parameters:
    -----------
    df : pd.DataFrame
        シミュレーション結果データフレーム

    Returns:
    --------
    pd.DataFrame
        月別サマリー
    """
    df = df.copy()
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['month'] = df['datetime'].dt.to_period('M')

    agg_dict = {
        'pv_generation_kwh': 'sum',
        'export_kwh': 'sum',
        'revenue_yen': 'sum',
    }

    if 'battery_charge_kwh' in df.columns:
        agg_dict['battery_charge_kwh'] = 'sum'
    if 'battery_discharge_kwh' in df.columns:
        agg_dict['battery_discharge_kwh'] = 'sum'

    monthly = df.groupby('month').agg(agg_dict).reset_index()

    monthly['average_price_yen_per_kwh'] = monthly['revenue_yen'] / monthly['export_kwh']
    monthly['month'] = monthly['month'].astype(str)

    return monthly


def calculate_hourly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    時間帯別サマリーを計算

    Parameters:
    -----------
    df : pd.DataFrame
        シミュレーション結果データフレーム

    Returns:
    --------
    pd.DataFrame
        時間帯別サマリー
    """
    df = df.copy()
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['hour'] = df['datetime'].dt.hour

    hourly = df.groupby('hour').agg({
        'pv_generation_kwh': 'sum',
        'export_kwh': 'sum',
        'revenue_yen': 'sum',
    }).reset_index()

    hourly['average_price_yen_per_kwh'] = hourly['revenue_yen'] / hourly['export_kwh']

    return hourly

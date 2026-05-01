"""太陽光発電プロファイル処理モジュール"""
import pandas as pd
from typing import Optional


def convert_hourly_to_30min(df: pd.DataFrame) -> pd.DataFrame:
    """
    1時間発電量データを30分データに変換

    Parameters:
    -----------
    df : pd.DataFrame
        columns: ['datetime', 'generation_kwh']

    Returns:
    --------
    pd.DataFrame
        30分単位のデータフレーム
    """
    result = []

    df['datetime'] = pd.to_datetime(df['datetime'])

    for _, row in df.iterrows():
        dt = row['datetime']
        generation = row['generation_kwh']

        # 1時間の発電量を2つの30分コマに等分
        result.append({
            'datetime': dt.strftime('%Y-%m-%d %H:00'),
            'generation_kwh': generation / 2.0
        })

        # 30分後のデータ
        dt_30 = dt + pd.Timedelta(minutes=30)
        result.append({
            'datetime': dt_30.strftime('%Y-%m-%d %H:%M'),
            'generation_kwh': generation / 2.0
        })

    result_df = pd.DataFrame(result)
    result_df['datetime'] = pd.to_datetime(result_df['datetime'])
    result_df = result_df.sort_values('datetime').reset_index(drop=True)

    return result_df


def apply_area_solar_correction(
    pv_df: pd.DataFrame,
    area_solar_df: pd.DataFrame,
    target_month: str
) -> pd.DataFrame:
    """
    エリア太陽光実績による月間発電量補正

    Parameters:
    -----------
    pv_df : pd.DataFrame
        発電所の30分発電量データ columns: ['datetime', 'generation_kwh']
    area_solar_df : pd.DataFrame
        エリア太陽光実績データ columns: ['datetime', 'generation_kwh']
    target_month : str
        対象月 (例: '2025-07')

    Returns:
    --------
    pd.DataFrame
        補正後の30分発電量データ
    """
    pv_df = pv_df.copy()
    area_solar_df = area_solar_df.copy()

    pv_df['datetime'] = pd.to_datetime(pv_df['datetime'])
    area_solar_df['datetime'] = pd.to_datetime(area_solar_df['datetime'])

    # 対象月のデータを抽出
    pv_month = pv_df[pv_df['datetime'].dt.strftime('%Y-%m') == target_month].copy()
    area_month = area_solar_df[area_solar_df['datetime'].dt.strftime('%Y-%m') == target_month].copy()

    if len(pv_month) == 0 or len(area_month) == 0:
        return pv_df

    # 発電所の月間発電量合計
    monthly_pv_total_kwh = pv_month['generation_kwh'].sum()

    # エリア太陽光の月間発電量合計
    area_solar_monthly_total = area_month['generation_kwh'].sum()

    if area_solar_monthly_total == 0:
        return pv_df

    # エリア太陽光実績による比率を計算
    area_month = area_month.set_index('datetime')
    area_month['ratio'] = area_month['generation_kwh'] / area_solar_monthly_total

    # 補正を適用
    pv_month = pv_month.set_index('datetime')
    pv_month = pv_month.join(area_month[['ratio']], how='left')
    pv_month['generation_kwh'] = monthly_pv_total_kwh * pv_month['ratio']
    pv_month = pv_month.drop(columns=['ratio']).reset_index()

    # 元のデータフレームの該当月を置き換え
    pv_df = pv_df[pv_df['datetime'].dt.strftime('%Y-%m') != target_month]
    pv_df = pd.concat([pv_df, pv_month], ignore_index=True)
    pv_df = pv_df.sort_values('datetime').reset_index(drop=True)

    return pv_df


def validate_pv_csv(df: pd.DataFrame) -> tuple[bool, str]:
    """
    太陽光発電量CSVの妥当性検証

    Returns:
    --------
    tuple[bool, str]
        (検証結果, エラーメッセージ)
    """
    # 必須列のチェック
    if 'datetime' not in df.columns:
        return False, "datetime列が見つかりません"

    if 'generation_kwh' not in df.columns and 'generation_kw' not in df.columns:
        return False, "generation_kwhまたはgeneration_kw列が見つかりません"

    # generation_kwがある場合はgeneration_kwhに変換
    if 'generation_kw' in df.columns and 'generation_kwh' not in df.columns:
        df['generation_kwh'] = df['generation_kw']

    # 日時のパース可能性チェック
    try:
        pd.to_datetime(df['datetime'])
    except Exception as e:
        return False, f"datetime列のパースに失敗: {str(e)}"

    # 発電量が数値かチェック
    try:
        pd.to_numeric(df['generation_kwh'])
    except Exception as e:
        return False, f"generation_kwh列が数値ではありません: {str(e)}"

    return True, "OK"


def resample_to_30min(df: pd.DataFrame) -> pd.DataFrame:
    """
    任意の時間間隔のデータを30分間隔にリサンプル

    Parameters:
    -----------
    df : pd.DataFrame
        columns: ['datetime', 'generation_kwh']

    Returns:
    --------
    pd.DataFrame
        30分間隔のデータフレーム
    """
    df = df.copy()
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.set_index('datetime')

    # 30分間隔にリサンプル（線形補間）
    df_resampled = df.resample('30min').interpolate(method='linear')
    df_resampled = df_resampled.reset_index()

    return df_resampled

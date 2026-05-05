"""データ正規化モジュール"""
import pandas as pd
from datetime import datetime


def parse_jepx_csv(file_path: str) -> pd.DataFrame:
    """JEPXのCSVファイルを解析してデータフレームに変換"""
    # JEPXのCSVは特殊なフォーマットなので、適切に解析する必要がある
    # ここでは基本的な実装を提供
    df = pd.read_csv(file_path, encoding='shift-jis', skiprows=1)

    # 必要な列を抽出し、標準化
    result = []

    for _, row in df.iterrows():
        date_str = str(row[0])  # 日付列

        # 各エリアの価格を処理
        for slot in range(1, 49):  # 30分コマは1日48コマ
            time = f"{(slot-1)//2:02d}:{((slot-1)%2)*30:02d}"
            dt_str = f"{date_str} {time}"

            result.append({
                'datetime': dt_str,
                'date': date_str,
                'slot': slot,
                'area': '東京',  # 実際にはCSVから取得
                'area_price_yen_per_kwh': None,  # 実際にはCSVから取得
                'system_price_yen_per_kwh': None,
                'source_url': file_path,
                'created_at': datetime.now().isoformat()
            })

    return pd.DataFrame(result)


def parse_area_generation_csv(file_path: str, area: str) -> pd.DataFrame:
    """エリア需給実績CSVを解析してデータフレームに変換"""
    # 各電力会社のフォーマットが異なるため、基本的な実装を提供
    df = pd.read_csv(file_path)

    result = []

    # CSVから日時、電源種別、発電量を抽出
    # 実際の実装では各電力会社のフォーマットに応じた処理が必要
    for _, row in df.iterrows():
        dt_str = str(row.get('datetime', row.get('日時', '')))

        # 各電源種別のデータを処理
        for source_type in ['太陽光', '風力', '水力']:
            generation_kw = row.get(source_type, 0)
            generation_kwh = generation_kw * 0.5  # kW平均値をkWhに変換

            result.append({
                'datetime': dt_str,
                'date': dt_str.split()[0],
                'slot': 1,  # 実際には計算が必要
                'area': area,
                'source_type': source_type,
                'generation_kw_avg': generation_kw,
                'generation_kwh': generation_kwh,
                'source_url': file_path,
                'created_at': datetime.now().isoformat()
            })

    return pd.DataFrame(result)


def kw_to_kwh_30min(kw_avg: float) -> float:
    """kW平均値を30分のkWhに変換"""
    return kw_avg * 0.5


def validate_datetime_format(dt_str: str) -> bool:
    """日時フォーマットを検証"""
    try:
        datetime.fromisoformat(dt_str.replace(' ', 'T'))
        return True
    except ValueError:
        return False


def fill_missing_slots(df: pd.DataFrame, start_date: str, end_date: str) -> pd.DataFrame:
    """欠損している30分コマを補完"""
    # 期間内の全30分コマを生成
    date_range = pd.date_range(start=start_date, end=end_date, freq='30min')

    # 既存データとマージ
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.set_index('datetime')
    df = df.reindex(date_range, fill_value=0)
    df = df.reset_index()
    df = df.rename(columns={'index': 'datetime'})

    return df


def aggregate_hourly_to_30min(df: pd.DataFrame) -> pd.DataFrame:
    """1時間データを30分データに分割"""
    result = []

    for _, row in df.iterrows():
        dt = pd.to_datetime(row['datetime'])
        generation = row['generation_kwh']

        # 1時間を2つの30分コマに分割
        result.append({
            'datetime': dt.strftime('%Y-%m-%d %H:00'),
            'generation_kwh': generation / 2
        })
        result.append({
            'datetime': dt.strftime('%Y-%m-%d %H:30'),
            'generation_kwh': generation / 2
        })

    return pd.DataFrame(result)

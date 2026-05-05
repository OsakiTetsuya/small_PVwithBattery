"""エリア別発電実績データ取得モジュール"""
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# エリアごとのデータ取得URL
AREA_URLS = {
    "北海道": "https://denkiyoho.hepco.co.jp/area_forecast.html",
    "東北": "https://setsuden.nw.tohoku-epco.co.jp/realtime_jukyu.html",
    "東京": "https://www.tepco.co.jp/forecast/html/area_jukyu-j.html",
    "中部": "https://powergrid.chuden.co.jp/denkiyoho/index.html",
    "北陸": "https://www.rikuden.co.jp/nw/denki-yoho/sp/results_jyukyu.html",
    "関西": "https://www.kansai-td.co.jp/denkiyoho/area-performance/index.html",
    "中国": "https://www.energia.co.jp/nw/jukyuu/eria_jukyu.html",
    "四国": "https://www.yonden.co.jp/nw/supply_demand/",
    "九州": "https://www.kyuden.co.jp/td_area_jukyu/jukyu.html",
}


class AreaGenerationFetcher:
    """エリア別発電実績データ取得クラス"""

    def __init__(self, save_dir: str = None):
        """
        Parameters:
        -----------
        save_dir : str
            データ保存先ディレクトリ（Noneの場合はdata/raw/area_generation）
        """
        if save_dir is None:
            try:
                from src.config import RAW_DATA_DIR
                save_dir = os.path.join(RAW_DATA_DIR, "area_generation")
            except ImportError:
                # スタンドアロン実行時
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                save_dir = os.path.join(base_dir, "data", "raw", "area_generation")

        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)

    def fetch_tokyo_area_data(self, target_date: str = None) -> Optional[pd.DataFrame]:
        """
        東京電力エリアの需給実績データを取得

        Parameters:
        -----------
        target_date : str
            対象日（YYYY-MM-DD形式）。Noneの場合は前日のデータ

        Returns:
        --------
        pd.DataFrame or None
            取得したデータフレーム
        """
        try:
            if target_date is None:
                target_date = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
            else:
                target_date = datetime.strptime(target_date, '%Y-%m-%d').strftime('%Y%m%d')

            # 東京電力のCSVダウンロードURL
            # 例: https://www.tepco.co.jp/forecast/html/images/juyo-2024xxxx.csv
            csv_url = f"https://www.tepco.co.jp/forecast/html/images/juyo-{target_date}.csv"

            logger.info(f"東京エリアデータ取得中: {csv_url}")

            response = requests.get(csv_url, timeout=30)
            response.raise_for_status()

            # Shift-JISエンコーディングでCSVを読み込み
            from io import StringIO
            csv_data = response.content.decode('shift-jis')

            # CSVをパース（ヘッダー行をスキップ）
            df = pd.read_csv(StringIO(csv_data), skiprows=1)

            # データを標準化
            normalized_df = self._normalize_tokyo_data(df, target_date)

            # ファイルに保存
            save_path = os.path.join(self.save_dir, f"tokyo_{target_date}.csv")
            normalized_df.to_csv(save_path, index=False, encoding='utf-8-sig')
            logger.info(f"データ保存完了: {save_path}")

            return normalized_df

        except requests.exceptions.RequestException as e:
            logger.error(f"東京エリアデータ取得エラー: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"東京エリアデータ処理エラー: {str(e)}")
            return None

    def _normalize_tokyo_data(self, df: pd.DataFrame, date_str: str) -> pd.DataFrame:
        """
        東京電力のCSVデータを標準化

        Parameters:
        -----------
        df : pd.DataFrame
            元のデータフレーム
        date_str : str
            日付文字列（YYYYMMDD形式）

        Returns:
        --------
        pd.DataFrame
            標準化されたデータフレーム
        """
        result = []

        # 日付をYYYY-MM-DD形式に変換
        date_formatted = datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d')

        # 各行を処理
        for _, row in df.iterrows():
            try:
                # 時刻を取得（例: "00:00" または "0:00"）
                time_str = str(row.get('時刻', row.iloc[0]))

                # datetime文字列を作成
                dt_str = f"{date_formatted} {time_str}"

                # 各電源種別のデータを抽出
                source_types_map = {
                    '太陽光': ['太陽光', 'solar', 'ソーラー'],
                    '風力': ['風力', 'wind'],
                    '水力': ['水力', 'hydro'],
                    '火力': ['火力', 'thermal', 'LNG'],
                    '原子力': ['原子力', 'nuclear'],
                    'その他': ['その他', 'other', '揚水', 'バイオマス']
                }

                for source_type, possible_cols in source_types_map.items():
                    generation_kw = 0

                    # 可能性のある列名から値を取得
                    for col_name in possible_cols:
                        for col in df.columns:
                            if col_name in col:
                                try:
                                    generation_kw = float(row[col])
                                    break
                                except (ValueError, TypeError):
                                    continue
                        if generation_kw > 0:
                            break

                    # kW平均値をkWhに変換（30分値なので0.5倍）
                    generation_kwh = generation_kw * 0.5

                    result.append({
                        'datetime': dt_str,
                        'date': date_formatted,
                        'area': '東京',
                        'source_type': source_type,
                        'generation_kw_avg': generation_kw,
                        'generation_kwh': generation_kwh,
                        'source_url': f"https://www.tepco.co.jp/forecast/html/images/juyo-{date_str}.csv",
                        'created_at': datetime.now().isoformat()
                    })

            except Exception as e:
                logger.warning(f"行の処理中にエラー: {str(e)}")
                continue

        return pd.DataFrame(result)

    def fetch_area_data_generic(self, area: str, target_date: str = None) -> Optional[pd.DataFrame]:
        """
        各エリアの需給実績データを取得（汎用メソッド）

        Parameters:
        -----------
        area : str
            エリア名（北海道、東北、東京、中部、北陸、関西、中国、四国、九州）
        target_date : str
            対象日（YYYY-MM-DD形式）

        Returns:
        --------
        pd.DataFrame or None
            取得したデータフレーム
        """
        # 東京エリアは専用メソッドを使用
        if area == "東京":
            return self.fetch_tokyo_area_data(target_date)

        # その他のエリアは今後実装
        logger.info(f"{area}エリアのデータ取得は現在開発中です")
        logger.info(f"データ所在地: {AREA_URLS.get(area, '不明')}")
        logger.info("手動でCSVをダウンロードしてアップロードしてください")

        return None

    def fetch_all_areas(self, target_date: str = None) -> Dict[str, pd.DataFrame]:
        """
        全エリアの需給実績データを取得

        Parameters:
        -----------
        target_date : str
            対象日（YYYY-MM-DD形式）

        Returns:
        --------
        Dict[str, pd.DataFrame]
            各エリアのデータフレームの辞書
        """
        results = {}

        for area in AREA_URLS.keys():
            logger.info(f"\n{area}エリアのデータを取得中...")
            df = self.fetch_area_data_generic(area, target_date)

            if df is not None:
                results[area] = df
                logger.info(f"✓ {area}エリア: {len(df)}件のデータを取得")
            else:
                logger.warning(f"✗ {area}エリア: データ取得失敗")

        return results

    def save_to_database(self, df: pd.DataFrame) -> bool:
        """
        取得したデータをデータベースに保存

        Parameters:
        -----------
        df : pd.DataFrame
            保存するデータフレーム

        Returns:
        --------
        bool
            保存成功の可否
        """
        try:
            try:
                from src.db import save_area_generation
            except ImportError:
                import sys
                sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from src.db import save_area_generation

            # スロット番号を計算
            df['datetime'] = pd.to_datetime(df['datetime'])
            df['slot'] = df['datetime'].dt.hour * 2 + df['datetime'].dt.minute // 30

            # データベースに保存
            save_area_generation(df)
            logger.info(f"データベースに{len(df)}件のデータを保存しました")

            return True

        except Exception as e:
            logger.error(f"データベース保存エラー: {str(e)}")
            return False


def fetch_area_generation_data(
    area: str,
    start_date: str,
    end_date: str,
    save_to_db: bool = True
) -> Optional[pd.DataFrame]:
    """
    エリア別発電実績データを期間指定で取得

    Parameters:
    -----------
    area : str
        エリア名
    start_date : str
        開始日（YYYY-MM-DD形式）
    end_date : str
        終了日（YYYY-MM-DD形式）
    save_to_db : bool
        データベースに保存するか

    Returns:
    --------
    pd.DataFrame or None
        取得したデータフレーム
    """
    fetcher = AreaGenerationFetcher()

    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')

    all_data = []

    # 日付範囲でループ
    current_date = start
    while current_date <= end:
        date_str = current_date.strftime('%Y-%m-%d')
        logger.info(f"\n{area}エリア {date_str} のデータを取得中...")

        df = fetcher.fetch_area_data_generic(area, date_str)

        if df is not None and len(df) > 0:
            all_data.append(df)

            if save_to_db:
                fetcher.save_to_database(df)

        current_date += timedelta(days=1)

    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        logger.info(f"\n合計 {len(combined_df)} 件のデータを取得しました")
        return combined_df
    else:
        logger.warning("データを取得できませんでした")
        return None


if __name__ == "__main__":
    # テスト実行
    print("=" * 60)
    print("エリア別発電実績データ取得モジュール - テスト")
    print("=" * 60)

    fetcher = AreaGenerationFetcher()

    # 東京エリアのデータを取得（前日）
    print("\n東京エリアのデータを取得中...")
    df = fetcher.fetch_tokyo_area_data()

    if df is not None:
        print(f"\n✓ データ取得成功: {len(df)}件")
        print("\nデータサンプル:")
        print(df.head(10))
        print("\n電源種別:")
        print(df['source_type'].value_counts())
    else:
        print("\n✗ データ取得失敗")
        print("\n手動でデータを取得する場合:")
        print("1. https://www.tepco.co.jp/forecast/html/area_jukyu-j.html にアクセス")
        print("2. CSVファイルをダウンロード")
        print("3. アプリの「データ取得」ページからアップロード")

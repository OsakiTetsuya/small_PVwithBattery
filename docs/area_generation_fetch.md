# エリア別発電実績データ取得機能

## 概要

各電力エリアの発電実績データを自動取得する機能です。現在は東京電力エリアのみ対応しています。

## 実装状況

### ✅ 対応済みエリア

- **東京電力エリア**: CSVダウンロードによる自動取得に対応

### 🔄 今後の対応予定

以下のエリアは現在開発中です。各電力会社のウェブサイトからCSVを手動ダウンロードしてアップロードしてください。

| エリア | データ所在地 | 対応状況 |
|--------|-------------|----------|
| 北海道 | https://denkiyoho.hepco.co.jp/area_forecast.html | 開発予定 |
| 東北 | https://setsuden.nw.tohoku-epco.co.jp/realtime_jukyu.html | 開発予定 |
| 東京 | https://www.tepco.co.jp/forecast/html/area_jukyu-j.html | ✅ 対応済み |
| 中部 | https://powergrid.chuden.co.jp/denkiyoho/index.html | 開発予定 |
| 北陸 | https://www.rikuden.co.jp/nw/denki-yoho/sp/results_jyukyu.html | 開発予定 |
| 関西 | https://www.kansai-td.co.jp/denkiyoho/area-performance/index.html | 開発予定 |
| 中国 | https://www.energia.co.jp/nw/jukyuu/eria_jukyu.html | 開発予定 |
| 四国 | https://www.yonden.co.jp/nw/supply_demand/ | 開発予定 |
| 九州 | https://www.kyuden.co.jp/td_area_jukyu/jukyu.html | 開発予定 |

## 使用方法

### 1. Streamlitアプリでの使用

#### 東京エリアの自動取得

```python
# アプリの「データ取得」ページで:
1. 「エリア発電実績データ」タブを選択
2. 「自動データ取得」セクションで「東京」を選択
3. 取得日を指定
4. 「データ取得」ボタンをクリック
```

#### その他エリアの手動アップロード

```python
1. 各電力会社のウェブサイトからCSVをダウンロード
2. 「CSVアップロード」セクションでエリアを選択
3. CSVファイルをアップロード
4. 「データベースに保存」ボタンをクリック
```

### 2. Pythonコードでの使用

```python
from src.fetch_area_generation import AreaGenerationFetcher, fetch_area_generation_data

# 単一日のデータ取得
fetcher = AreaGenerationFetcher()
df = fetcher.fetch_tokyo_area_data('2025-07-01')

if df is not None:
    print(f"取得件数: {len(df)}")
    # データベースに保存
    fetcher.save_to_database(df)

# 期間指定でデータ取得
df = fetch_area_generation_data(
    area='東京',
    start_date='2025-07-01',
    end_date='2025-07-07',
    save_to_db=True
)
```

## データフォーマット

### 入力フォーマット（手動アップロード用）

```csv
datetime,source_type,generation_kwh
2025-07-01 10:00,太陽光,5000
2025-07-01 10:30,太陽光,5200
2025-07-01 11:00,風力,1500
```

### 出力フォーマット（データベース保存形式）

```csv
datetime,date,area,source_type,generation_kw_avg,generation_kwh,source_url,created_at,slot
2025-07-01 10:00,2025-07-01,東京,太陽光,10000,5000,https://...,2025-07-01T10:00:00,20
```

## 電源種別

以下の電源種別をサポートしています:

- 太陽光
- 風力
- 水力
- 火力LNG
- 火力石炭
- 火力石油
- バイオマス
- 原子力
- 地熱
- 揚水
- 蓄電池
- 連系線
- その他

## データ変換

### kW → kWh変換

各電力会社の需給実績データは、30分値について「kW値を30分平均した値」を基に公開しています。
したがって、売上計算用のkWhに変換する場合は、以下の式を使用します:

```
kWh = kW平均値 × 0.5
```

## エラーハンドリング

### よくあるエラーと対処法

1. **ネットワークエラー**
   ```
   エラー: HTTPSConnectionPool...
   ```
   - 対処: インターネット接続を確認してください
   - または: 手動CSVアップロードをご利用ください

2. **データが見つからない**
   ```
   エラー: データ取得に失敗しました
   ```
   - 対処: 指定日のデータが公開されているか確認してください
   - または: 別の日付を試してください

3. **CSVフォーマットエラー**
   ```
   エラー: 必須列が不足しています
   ```
   - 対処: CSVファイルに以下の列が含まれているか確認してください:
     - datetime
     - source_type
     - generation_kwh

## 技術詳細

### 東京電力エリアのデータ取得

東京電力は以下のURLでCSVファイルを公開しています:

```
https://www.tepco.co.jp/forecast/html/images/juyo-YYYYMMDD.csv
```

- エンコーディング: Shift-JIS
- 形式: 30分単位の需給実績
- 更新頻度: 日次

### 実装ファイル

- `src/fetch_area_generation.py`: データ取得ロジック
- `app.py`: Streamlit UI統合
- `src/db.py`: データベース保存機能

## 今後の拡張

### 予定している機能

1. **他エリアの自動取得対応**
   - 北海道、東北、中部、北陸、関西、中国、四国、九州の順に対応予定

2. **バッチ処理機能**
   - 複数日のデータを一括取得
   - 定期的な自動更新

3. **データ品質チェック**
   - 欠損値の検出と補完
   - 異常値の検出

4. **リトライ機能**
   - ネットワークエラー時の自動リトライ
   - バックオフ戦略

## 参考リンク

- [OCCTO - 供給区域別需給実績](https://www.occto.or.jp/news/oshirase_sonotaoshirase_2016_170106_juyojisseki.html)
- [東京電力 - エリア需給実績](https://www.tepco.co.jp/forecast/html/area_jukyu-j.html)
- [東京電力 - 電源種別、30分値の説明](https://www.tepco.co.jp/forecast/html/area_data-j.html)

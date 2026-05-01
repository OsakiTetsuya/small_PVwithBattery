# 低圧太陽光＋DCリンク蓄電池 JEPX売上シミュレーター 仕様書

## 1. 目的

低圧太陽光発電所の1時間周期発電量データ、JEPXスポット市場価格、各電力エリアの電源別発電実績データ、DCリンク蓄電池の充放電制御を組み合わせ、JEPX価格連動で売電した場合の売上をシミュレーションする。

ローカルPC上でPythonアプリとして動作し、Streamlitで可視化する。

---

## 2. 対象範囲

### 2.1 対象市場

JEPXスポット市場を対象とする。  
JEPXのスポット市場データには、30分コマごとのシステムプライスおよびエリアプライスがある。対象エリアは北海道、東北、東京、中部、北陸、関西、中国、四国、九州である。  
[https://www.jepx.jp/electricpower/market-data/spot/]

CSVデータ例：  
[https://www.jepx.jp/market/excel/spot_2023.csv]

### 2.2 対象エリア

JEPXエリアプライスが存在する以下9エリアを対象とする。

- 北海道
- 東北
- 東京
- 中部
- 北陸
- 関西
- 中国
- 四国
- 九州

※沖縄はエリア需給実績データは存在するが、JEPXスポット市場のエリアプライス対象外のため、MVPでは売上計算対象外とする。

### 2.3 データ期間

取得・保持するデータは直近2年分とする。

例：

- JEPXスポット市場価格：直近2年分
- 各エリア需給実績：直近2年分
- 発電所シミュレーション対象期間：ユーザーが選択

---

## 3. データ所在地

### 3.1 JEPX市場価格データ

| データ | 所在地 | 備考 |
|---|---|---|
| JEPXスポット市場データ | https://www.jepx.jp/electricpower/market-data/spot/ | 30分コマ、システムプライス、エリアプライスを取得する |
| JEPX CSV例 | https://www.jepx.jp/market/excel/spot_2023.csv | 年度または年単位CSV。実装では公式ページからダウンロードリンクを取得すること |

JEPXスポット市場ページでは、30分コマ、日平均、月平均、年度平均の切替があり、エリアプライスとして北海道、東北、東京、中部、北陸、関西、中国、四国、九州が表示される。  
[https://www.jepx.jp/electricpower/market-data/spot/]

---

### 3.2 エリア別・電源別発電量データ

各一般送配電事業者が「エリア需給実績データ」として公開しているデータを使用する。  
OCCTOは供給区域別の需給実績について、各事業者サイトへのリンクをまとめている。  
[https://www.occto.or.jp/news/oshirase_sonotaoshirase_2016_170106_juyojisseki.html]

| エリア | データ所在地 | 備考 |
|---|---|---|
| 北海道 | https://denkiyoho.hepco.co.jp/area_forecast.html | 北海道エリアのでんき予報 |
| 東北 | https://setsuden.nw.tohoku-epco.co.jp/realtime_jukyu.html | エリア需給実績データ |
| 東京 | https://www.tepco.co.jp/forecast/html/area_jukyu-j.html | エリア需給実績データ、30分毎CSV |
| 東京 当日説明 | https://www.tepco.co.jp/forecast/html/area_data-j.html | 電源種別、30分値の説明 |
| 中部 | https://powergrid.chuden.co.jp/denkiyoho/index.html | でんき予報、過去実績データ |
| 北陸 | https://www.rikuden.co.jp/nw/denki-yoho/sp/results_jyukyu.html | 北陸エリア需給実績 |
| 関西 | https://www.kansai-td.co.jp/denkiyoho/area-performance/index.html | 関西エリア需給実績 |
| 中国 | https://www.energia.co.jp/nw/jukyuu/eria_jukyu.html | 供給区域の需給実績 |
| 四国 | https://www.yonden.co.jp/nw/supply_demand/ | 四国エリア需給実績 |
| 九州 | https://www.kyuden.co.jp/td_area_jukyu/jukyu.html | エリア需給実績データ |
| 沖縄参考 | http://www.okiden.co.jp/business-support/service/supply-and-demand/index.html | JEPX対象外だが需給実績は存在 |

各社の需給実績データは、30分値について「kW値を30分平均した値」を基に公開している。したがって、売上計算用のkWhに変換する場合は、原則として `kWh = kW平均値 × 0.5` とする。  
[https://www.tepco.co.jp/forecast/html/area_data-j.html]  
[https://www.kyuden.co.jp/td_area_jukyu/jukyu.html]  
[https://www.kansai-td.co.jp/denkiyoho/area-performance/index.html]

---

## 4. 使用技術

MVPは以下で実装する。

- Python
- pandas
- SQLite
- SQLAlchemy
- Streamlit
- Plotly
- requests
- BeautifulSoup
- openpyxl

---

## 5. アプリ構成

ローカルPCで以下のように起動する。

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 6. ディレクトリ構成

project/
  app.py
  README.md
  CLAUDE.md
  requirements.txt
  data/
    raw/
      jepx/
      area_generation/
      pv_uploads/
    processed/
    app.db
  src/
    config.py
    db.py
    fetch_jepx.py
    fetch_area_generation.py
    normalize.py
    pv_profile.py
    battery.py
    revenue.py
    visualization.py
  docs/
    spec.md

## 7.入力データ

### 7.1 低圧太陽光発電量データ
ユーザーがCSVでアップロードする。


基本形式：
datetime,generation_kwh
2025-07-01 00:00,0
2025-07-01 01:00,0
2025-07-01 12:00,35.2
入力データは1時間周期とする。

##8. 1時間データから30分データへの変換
JEPXは30分コマのため、太陽光発電量も30分単位に変換する。


基本変換：


1時間発電量を2等分する。

例：
10:00-11:00 20kWh

変換後：
10:00-10:30 10kWh
10:30-11:00 10kWh

## 9. エリア太陽光実績による発電プロファイル補正
対象月の発電所シミュレーション月間発電量を monthly_pv_total_kwh とする。


対象エリアの太陽光実績30分データを area_solar_kwh[t] とする。


area_solar_monthly_total = 対象月のarea_solar_kwh合計

ratio[t] = area_solar_kwh[t] / area_solar_monthly_total

補正後PV発電量[t] = monthly_pv_total_kwh × ratio[t]


これにより、月間発電量は元のシミュレーション値と一致しつつ、30分ごとの発電パターンは対象年月・対象エリアの実績に近づく。

## 10. データベース設計
10.1 market_prices

CREATE TABLE market_prices (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  datetime TEXT NOT NULL,
  date TEXT NOT NULL,
  slot INTEGER NOT NULL,
  area TEXT NOT NULL,
  system_price_yen_per_kwh REAL,
  area_price_yen_per_kwh REAL,
  source_url TEXT,
  created_at TEXT
);


10.2 area_generation

CREATE TABLE area_generation (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  datetime TEXT NOT NULL,
  date TEXT NOT NULL,
  slot INTEGER NOT NULL,
  area TEXT NOT NULL,
  source_type TEXT NOT NULL,
  generation_kw_avg REAL,
  generation_kwh REAL,
  source_url TEXT,
  created_at TEXT
);


10.3 pv_profiles

CREATE TABLE pv_profiles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  plant_name TEXT NOT NULL,
  datetime TEXT NOT NULL,
  generation_kwh REAL NOT NULL,
  generation_type TEXT,
  created_at TEXT
);


10.4 simulation_results

CREATE TABLE simulation_results (
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
);

## 11. 蓄電池シミュレーション仕様

### 11.1 前提

低圧太陽光にDCリンク蓄電池を併設する。
蓄電池は太陽光発電から充電する。
系統からの充電はMVPでは行わない。
昼間に満充電になるように充電する。
JEPX価格が高い時間帯に最大出力で放電する。
売上はJEPXエリアプライスのみで計算する。
託送料、手数料、インバランス、消費税は考慮しない。


### 11.2 蓄電池入力パラメータ

項目	単位	内容
battery_capacity_kwh	kWh	蓄電池容量
max_charge_kw	kW	最大充電出力
max_discharge_kw	kW	最大放電出力
charge_efficiency	%	充電効率
discharge_efficiency	%	放電効率
initial_soc_percent	%	初期SOC
min_soc_percent	%	最小SOC
max_soc_percent	%	最大SOC
pcs_capacity_kw	kW	PCS容量
grid_export_limit_kw	kW	系統売電上限
operation_mode	text	price_optimized


### 11.3 30分コマ換算

30分あたり最大充電量_kWh = max_charge_kw × 0.5
30分あたり最大放電量_kWh = max_discharge_kw × 0.5
30分あたり売電上限_kWh = grid_export_limit_kw × 0.5
PCS上限_kWh = pcs_capacity_kw × 0.5



### 11.4 運転ロジック

日単位で最適化する。


対象日のJEPXエリアプライスを取得する。
価格が高い30分コマを放電候補とする。
放電候補では、蓄電池が許す限り最大放電する。
放電候補までに、昼間の太陽光発電から蓄電池を満充電に近づける。
太陽光発電が売電上限を超える場合、超過分は優先的に充電する。
売電上限を超えていない場合でも、将来の高価格時間帯に備えて、低価格時間帯の太陽光を充電する。
放電時は、PCS容量および系統売電上限を超えないようにする。


### 11.5 放電時間帯の決定

MVPでは以下のどちらかを選べるようにする。


A. 上位価格コマ方式

対象日の価格が高い順に30分コマを並べる。
蓄電池容量と最大放電出力から放電可能コマ数を決める。
高価格順に最大放電する。


B. 価格しきい値方式

市場価格が指定しきい値以上のコマで放電する。
例：20円/kWh以上なら放電。


初期設定はAの上位価格コマ方式とする。



## 12. 売電量計算

30分ごとに以下を計算する。


pv_generation_kwh = 太陽光発電量
charge_kwh = 蓄電池充電量
discharge_kwh = 蓄電池放電量

export_kwh = pv_generation_kwh - charge_kwh + discharge_kwh
export_kwh = min(export_kwh, grid_export_limit_kw × 0.5)
export_kwh = min(export_kwh, pcs_capacity_kw × 0.5)
export_kwh = max(export_kwh, 0)



## 13. 売上計算

revenue_yen = export_kwh × area_price_yen_per_kwh


日別売上：


daily_revenue = 30分ごとのrevenue_yen合計


月別売上：


monthly_revenue = 日別売上合計


年間売上：


annual_revenue = 月別売上合計



## 14. 可視化要件

Streamlitで以下を表示する。


### 14.1 市場価格と発電量

横軸：日時
左軸：kWh
右軸：円/kWh
表示：
太陽光発電量
売電量
JEPXエリアプライス

### 14.2 蓄電池挙動

充電量
放電量
SOC
売電量

### 14.3 エリア需給・電源構成

太陽光
風力
水力
火力LNG
火力石炭
火力石油
バイオマス
原子力
地熱
揚水
蓄電池
連系線
その他
JEPX価格

### 14.4 売上分析

日別売上
月別売上
時間帯別売上
価格帯別売電量
蓄電池あり/なし比較


## 15. Streamlit画面

### 15.1 データ取得画面

機能：


JEPXデータ取得
エリア需給実績データ取得
取得済みデータ確認
欠損確認
CSV手動アップロード

自動取得が難しい電力会社ページについては、MVPでは手動CSVアップロードも許容する。



### 15.2 発電所登録画面

入力項目：


発電所名
エリア
太陽光容量 kW
PCS容量 kW
系統売電上限 kW
1時間発電量CSV
蓄電池有無
蓄電池容量 kWh
最大充電出力 kW
最大放電出力 kW
充放電効率
SOC範囲


### 15.3 シミュレーション画面

入力項目：


対象期間
対象エリア
発電所
補正方式
単純1時間→30分分割
エリア太陽光実績による月間補正
蓄電池運転方式
上位価格コマ方式
価格しきい値方式

出力：


総売上
月別売上
日別売上
発電量
売電量
蓄電池SOC
CSVダウンロード


## 16. CSV出力

datetime,area,market_price_yen_per_kwh,pv_generation_kwh,battery_charge_kwh,battery_discharge_kwh,battery_soc_kwh,export_kwh,revenue_yen
2025-07-01 10:00,東京,8.5,20.1,3.0,0,15.2,17.1,145.35



## 17. 受け入れ条件

MVP完了条件：


JEPXスポット市場価格を直近2年分取得できる。
JEPXエリアプライスを9エリア分保持できる。
各電力エリアの需給実績データを取得またはCSVアップロードできる。
電源別発電量を30分単位で正規化できる。
kW平均値をkWhに変換できる。
低圧太陽光の1時間データを30分データに変換できる。
エリア太陽光実績を使って、月間発電量を維持したまま30分プロファイル補正できる。
DCリンク蓄電池の充放電を計算できる。
高価格時間帯に最大放電するシミュレーションができる。
JEPX価格のみで売上計算できる。
Streamlitで市場価格、発電量、蓄電池挙動、売上を可視化できる。
結果CSVをダウンロードできる。

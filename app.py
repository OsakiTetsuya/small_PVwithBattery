"""JEPX売上シミュレーター Streamlitアプリ"""
import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta

# モジュールのインポート
from src import db
from src import config
from src import pv_profile
from src import battery
from src import revenue
from src import visualization

# ページ設定
st.set_page_config(
    page_title="JEPX売上シミュレーター",
    page_icon="⚡",
    layout="wide"
)

# データベース初期化
db.init_database()

# タイトル
st.title("⚡ 低圧太陽光＋DCリンク蓄電池 JEPX売上シミュレーター")

# サイドバーでページ選択
page = st.sidebar.selectbox(
    "ページを選択",
    ["ホーム", "データ取得", "発電所登録", "シミュレーション実行", "結果分析"]
)

# ===== ホームページ =====
if page == "ホーム":
    st.header("📊 ホーム")

    st.markdown("""
    ## このアプリについて

    低圧太陽光発電所とDCリンク蓄電池を組み合わせた場合のJEPX売上をシミュレーションするツールです。

    ### 主な機能

    1. **データ取得**: JEPX市場価格とエリア発電実績データの管理
    2. **発電所登録**: 太陽光発電所の発電量データを登録
    3. **シミュレーション実行**: 蓄電池運転をシミュレーションして売上を計算
    4. **結果分析**: 売上や蓄電池挙動を可視化

    ### 使い方

    1. 左のサイドバーから「データ取得」を選択し、市場価格データをアップロード
    2. 「発電所登録」で太陽光発電所の発電量データをアップロード
    3. 「シミュレーション実行」でシミュレーションを実行
    4. 「結果分析」で結果を確認・可視化

    ### データフォーマット

    - **JEPX市場価格CSV**: `datetime,area,area_price_yen_per_kwh`
    - **太陽光発電量CSV**: `datetime,generation_kwh`

    ### MVP版の制限事項

    - データ自動取得は未実装（CSV手動アップロードで代替）
    - エリア太陽光実績による補正は簡易実装
    - 託送料、手数料、インバランス等は考慮していません
    """)

# ===== データ取得ページ =====
elif page == "データ取得":
    st.header("📥 データ取得")

    tab1, tab2, tab3 = st.tabs(["市場価格データ", "エリア発電実績データ", "データ確認"])

    # タブ1: 市場価格データ
    with tab1:
        st.subheader("JEPX市場価格データ")

        st.markdown("""
        ### CSVアップロード

        以下のフォーマットでCSVファイルをアップロードしてください:

        ```
        datetime,area,area_price_yen_per_kwh
        2025-07-01 10:00,東京,8.5
        2025-07-01 10:30,東京,9.2
        ```

        必須列:
        - `datetime`: 日時 (YYYY-MM-DD HH:MM形式)
        - `area`: エリア名（北海道、東北、東京、中部、北陸、関西、中国、四国、九州）
        - `area_price_yen_per_kwh`: エリアプライス [円/kWh]
        """)

        uploaded_file = st.file_uploader(
            "JEPX市場価格CSVファイル",
            type=['csv'],
            key='jepx_upload'
        )

        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)

                # 必須列チェック
                required_cols = ['datetime', 'area', 'area_price_yen_per_kwh']
                if not all(col in df.columns for col in required_cols):
                    st.error(f"必須列が不足しています: {required_cols}")
                else:
                    st.success(f"{len(df)}件のデータを読み込みました")

                    # プレビュー
                    st.dataframe(df.head(20))

                    # データを保存
                    if st.button("データベースに保存", key='save_jepx'):
                        # 日付とスロット情報を追加
                        df['datetime'] = pd.to_datetime(df['datetime'])
                        df['date'] = df['datetime'].dt.date.astype(str)
                        df['slot'] = df['datetime'].dt.hour * 2 + df['datetime'].dt.minute // 30
                        df['system_price_yen_per_kwh'] = df.get('system_price_yen_per_kwh', None)
                        df['source_url'] = 'manual_upload'
                        df['created_at'] = datetime.now().isoformat()

                        db.save_market_prices(df)
                        st.success("データベースに保存しました")

            except Exception as e:
                st.error(f"エラー: {str(e)}")

    # タブ2: エリア発電実績データ
    with tab2:
        st.subheader("エリア発電実績データ")

        # 自動取得セクション
        st.markdown("### 🔄 自動データ取得（東京エリアのみ対応）")

        col1, col2 = st.columns([2, 1])

        with col1:
            fetch_area = st.selectbox("取得エリア", config.JEPX_AREAS, key='fetch_area_select')
            fetch_date = st.date_input("取得日", datetime.now() - timedelta(days=1), key='fetch_date')

        with col2:
            st.write("")
            st.write("")
            if st.button("データ取得", key='fetch_area_data', type='primary'):
                if fetch_area == "東京":
                    with st.spinner('東京エリアのデータを取得中...'):
                        try:
                            from src.fetch_area_generation import AreaGenerationFetcher

                            fetcher = AreaGenerationFetcher()
                            df = fetcher.fetch_tokyo_area_data(fetch_date.strftime('%Y-%m-%d'))

                            if df is not None and len(df) > 0:
                                st.success(f"✓ {len(df)}件のデータを取得しました")

                                # プレビュー
                                st.dataframe(df.head(20))

                                # データベースに保存
                                if fetcher.save_to_database(df):
                                    st.success("✓ データベースに保存しました")
                                else:
                                    st.warning("データベースへの保存に失敗しました")
                            else:
                                st.error("データ取得に失敗しました。手動アップロードをお試しください。")

                        except Exception as e:
                            st.error(f"エラー: {str(e)}")
                            st.info("💡 手動アップロードをお試しください")
                else:
                    st.info(f"{fetch_area}エリアの自動取得は現在開発中です。手動アップロードをご利用ください。")
                    st.markdown(f"""
                    **{fetch_area}エリアのデータ所在地:**
                    - 各電力会社のウェブサイトからCSVをダウンロードしてください
                    - 下記の「CSVアップロード」セクションからアップロードできます
                    """)

        st.markdown("---")

        st.markdown("""
        ### 📤 CSVアップロード

        以下のフォーマットでCSVファイルをアップロードしてください:

        ```
        datetime,source_type,generation_kwh
        2025-07-01 10:00,太陽光,5000
        2025-07-01 10:30,太陽光,5200
        ```

        必須列:
        - `datetime`: 日時 (YYYY-MM-DD HH:MM形式)
        - `source_type`: 電源種別（太陽光、風力、水力など）
        - `generation_kwh`: 発電量 [kWh]
        """)

        area_select = st.selectbox("エリア選択", config.JEPX_AREAS, key='area_gen_select')

        uploaded_file = st.file_uploader(
            "エリア発電実績CSVファイル",
            type=['csv'],
            key='area_gen_upload'
        )

        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)

                # 必須列チェック
                required_cols = ['datetime', 'source_type', 'generation_kwh']
                if not all(col in df.columns for col in required_cols):
                    st.error(f"必須列が不足しています: {required_cols}")
                else:
                    st.success(f"{len(df)}件のデータを読み込みました")

                    # プレビュー
                    st.dataframe(df.head(20))

                    # データを保存
                    if st.button("データベースに保存", key='save_area_gen'):
                        df['datetime'] = pd.to_datetime(df['datetime'])
                        df['date'] = df['datetime'].dt.date.astype(str)
                        df['slot'] = df['datetime'].dt.hour * 2 + df['datetime'].dt.minute // 30
                        df['area'] = area_select
                        df['generation_kw_avg'] = df['generation_kwh'] / 0.5
                        df['source_url'] = 'manual_upload'
                        df['created_at'] = datetime.now().isoformat()

                        db.save_area_generation(df)
                        st.success("データベースに保存しました")

            except Exception as e:
                st.error(f"エラー: {str(e)}")

    # タブ3: データ確認
    with tab3:
        st.subheader("データ確認")

        check_area = st.selectbox("エリア選択", config.JEPX_AREAS, key='check_area')
        check_start = st.date_input("開始日", datetime.now() - timedelta(days=30))
        check_end = st.date_input("終了日", datetime.now())

        if st.button("データ確認"):
            availability = db.check_data_availability(
                check_area,
                check_start.strftime('%Y-%m-%d'),
                check_end.strftime('%Y-%m-%d')
            )

            col1, col2 = st.columns(2)

            with col1:
                if availability['market_prices']:
                    st.success("✅ 市場価格データ: 利用可能")
                else:
                    st.error("❌ 市場価格データ: 利用不可")

            with col2:
                if availability['area_generation']:
                    st.success("✅ エリア発電実績データ: 利用可能")
                else:
                    st.error("❌ エリア発電実績データ: 利用不可")

# ===== 発電所登録ページ =====
elif page == "発電所登録":
    st.header("🏭 発電所登録")

    st.markdown("""
    ### 太陽光発電所の発電量データを登録

    1時間単位の発電量データをCSVでアップロードしてください。
    30分単位のデータに自動変換されます。

    ### CSVフォーマット

    ```
    datetime,generation_kwh
    2025-07-01 00:00,0
    2025-07-01 01:00,0
    2025-07-01 12:00,35.2
    ```
    """)

    plant_name = st.text_input("発電所名", "発電所1")
    plant_area = st.selectbox("設置エリア", config.JEPX_AREAS)

    col1, col2 = st.columns(2)
    with col1:
        pv_capacity_kw = st.number_input("太陽光容量 [kW]", min_value=0.0, value=50.0, step=1.0)
        pcs_capacity_kw = st.number_input("PCS容量 [kW]", min_value=0.0, value=50.0, step=1.0)

    with col2:
        grid_export_limit_kw = st.number_input("系統売電上限 [kW]", min_value=0.0, value=50.0, step=1.0)

    st.subheader("発電量データアップロード")

    uploaded_file = st.file_uploader(
        "1時間発電量CSVファイル",
        type=['csv'],
        key='pv_upload'
    )

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)

            # バリデーション
            is_valid, message = pv_profile.validate_pv_csv(df)

            if not is_valid:
                st.error(f"エラー: {message}")
            else:
                st.success(f"{len(df)}件のデータを読み込みました")

                # プレビュー
                st.dataframe(df.head(20))

                # 1時間→30分変換
                conversion_method = st.radio(
                    "変換方式",
                    ["単純1時間→30分分割", "エリア太陽光実績による補正（未実装）"]
                )

                if st.button("発電所を登録"):
                    # 30分データに変換
                    df_30min = pv_profile.convert_hourly_to_30min(df)

                    # データベースに保存
                    df_30min['generation_type'] = 'hourly_converted'
                    db.save_pv_profile(plant_name, df_30min)

                    # セッション状態に発電所情報を保存
                    if 'plant_configs' not in st.session_state:
                        st.session_state.plant_configs = {}

                    st.session_state.plant_configs[plant_name] = {
                        'area': plant_area,
                        'pv_capacity_kw': pv_capacity_kw,
                        'pcs_capacity_kw': pcs_capacity_kw,
                        'grid_export_limit_kw': grid_export_limit_kw
                    }

                    st.success(f"発電所「{plant_name}」を登録しました")

        except Exception as e:
            st.error(f"エラー: {str(e)}")

    # 登録済み発電所一覧
    st.subheader("登録済み発電所")

    plants = db.list_pv_profiles()

    if len(plants) == 0:
        st.info("登録済みの発電所はありません")
    else:
        for plant in plants:
            st.write(f"- {plant}")

# ===== シミュレーション実行ページ =====
elif page == "シミュレーション実行":
    st.header("⚙️ シミュレーション実行")

    # 登録済み発電所を取得
    plants = db.list_pv_profiles()

    if len(plants) == 0:
        st.warning("発電所が登録されていません。先に「発電所登録」ページで発電所を登録してください。")
    else:
        # シミュレーション設定
        st.subheader("シミュレーション設定")

        simulation_name = st.text_input("シミュレーション名", f"sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

        col1, col2 = st.columns(2)

        with col1:
            selected_plant = st.selectbox("発電所選択", plants)
            target_area = st.selectbox("対象エリア", config.JEPX_AREAS)

        with col2:
            start_date = st.date_input("開始日", datetime.now() - timedelta(days=7))
            end_date = st.date_input("終了日", datetime.now())

        # 蓄電池設定
        st.subheader("蓄電池設定")

        use_battery = st.checkbox("蓄電池を使用する", value=True)

        if use_battery:
            col1, col2, col3 = st.columns(3)

            with col1:
                battery_capacity = st.number_input(
                    "蓄電池容量 [kWh]",
                    min_value=0.0,
                    value=config.DEFAULT_BATTERY_CONFIG['battery_capacity_kwh'],
                    step=1.0
                )
                max_charge_kw = st.number_input(
                    "最大充電出力 [kW]",
                    min_value=0.0,
                    value=config.DEFAULT_BATTERY_CONFIG['max_charge_kw'],
                    step=1.0
                )
                max_discharge_kw = st.number_input(
                    "最大放電出力 [kW]",
                    min_value=0.0,
                    value=config.DEFAULT_BATTERY_CONFIG['max_discharge_kw'],
                    step=1.0
                )

            with col2:
                charge_eff = st.slider(
                    "充電効率",
                    min_value=0.5,
                    max_value=1.0,
                    value=config.DEFAULT_BATTERY_CONFIG['charge_efficiency'],
                    step=0.01
                )
                discharge_eff = st.slider(
                    "放電効率",
                    min_value=0.5,
                    max_value=1.0,
                    value=config.DEFAULT_BATTERY_CONFIG['discharge_efficiency'],
                    step=0.01
                )

            with col3:
                initial_soc = st.slider(
                    "初期SOC [%]",
                    min_value=0.0,
                    max_value=100.0,
                    value=config.DEFAULT_BATTERY_CONFIG['initial_soc_percent'],
                    step=1.0
                )
                min_soc = st.slider(
                    "最小SOC [%]",
                    min_value=0.0,
                    max_value=100.0,
                    value=config.DEFAULT_BATTERY_CONFIG['min_soc_percent'],
                    step=1.0
                )
                max_soc = st.slider(
                    "最大SOC [%]",
                    min_value=0.0,
                    max_value=100.0,
                    value=config.DEFAULT_BATTERY_CONFIG['max_soc_percent'],
                    step=1.0
                )

            # 運転方式
            st.subheader("運転方式")

            discharge_mode = st.radio(
                "放電方式",
                ["上位価格コマ方式", "価格しきい値方式"]
            )

            if discharge_mode == "上位価格コマ方式":
                num_discharge_slots = st.slider(
                    "放電スロット数",
                    min_value=1,
                    max_value=20,
                    value=8,
                    step=1
                )
                threshold = None
            else:
                threshold = st.number_input(
                    "価格しきい値 [円/kWh]",
                    min_value=0.0,
                    value=15.0,
                    step=0.5
                )
                num_discharge_slots = None

        # シミュレーション実行
        if st.button("シミュレーション実行", type="primary"):
            with st.spinner("シミュレーション中..."):
                try:
                    # 発電量データを取得
                    pv_df = db.get_pv_profile(selected_plant)

                    if len(pv_df) == 0:
                        st.error("発電量データが見つかりません")
                    else:
                        # 期間でフィルタ
                        pv_df['datetime'] = pd.to_datetime(pv_df['datetime'])
                        pv_df = pv_df[
                            (pv_df['datetime'] >= pd.Timestamp(start_date)) &
                            (pv_df['datetime'] <= pd.Timestamp(end_date))
                        ]

                        # 市場価格データを取得
                        prices_df = db.get_market_prices(
                            target_area,
                            start_date.strftime('%Y-%m-%d'),
                            end_date.strftime('%Y-%m-%d')
                        )

                        if len(prices_df) == 0:
                            st.error(f"市場価格データが見つかりません（エリア: {target_area}, 期間: {start_date} - {end_date}）")
                        else:
                            # 価格列名を統一
                            if 'area_price_yen_per_kwh' not in prices_df.columns and 'market_price_yen_per_kwh' in prices_df.columns:
                                prices_df['area_price_yen_per_kwh'] = prices_df['market_price_yen_per_kwh']

                            if use_battery:
                                # 蓄電池設定
                                battery_config = {
                                    'battery_capacity_kwh': battery_capacity,
                                    'max_charge_kw': max_charge_kw,
                                    'max_discharge_kw': max_discharge_kw,
                                    'charge_efficiency': charge_eff,
                                    'discharge_efficiency': discharge_eff,
                                    'initial_soc_percent': initial_soc,
                                    'min_soc_percent': min_soc,
                                    'max_soc_percent': max_soc,
                                    'pcs_capacity_kw': 50.0,
                                    'grid_export_limit_kw': 50.0,
                                    'operation_mode': 'price_optimized'
                                }

                                # 蓄電池シミュレーター作成
                                sim = battery.BatterySimulator(battery_config)

                                # シミュレーション実行
                                mode = 'top_price' if discharge_mode == "上位価格コマ方式" else 'threshold'

                                results_df = sim.simulate_period(
                                    pv_df,
                                    prices_df,
                                    discharge_mode=mode,
                                    threshold=threshold,
                                    num_discharge_slots=num_discharge_slots
                                )

                            else:
                                # 蓄電池なしの計算
                                results_df = revenue.calculate_revenue_without_battery(
                                    pv_df,
                                    prices_df,
                                    grid_export_limit_kw=50.0,
                                    pcs_capacity_kw=50.0
                                )

                            # 結果を保存
                            results_df['area'] = target_area
                            db.save_simulation_results(simulation_name, results_df)

                            # セッション状態に保存
                            st.session_state.latest_simulation = {
                                'name': simulation_name,
                                'results': results_df,
                                'use_battery': use_battery
                            }

                            st.success("シミュレーション完了！「結果分析」ページで結果を確認してください。")

                            # サマリーを表示
                            total_revenue = results_df['revenue_yen'].sum()
                            total_generation = results_df['pv_generation_kwh'].sum()
                            total_export = results_df['export_kwh'].sum()

                            col1, col2, col3 = st.columns(3)

                            with col1:
                                st.metric("総売上", f"¥{total_revenue:,.0f}")

                            with col2:
                                st.metric("総発電量", f"{total_generation:,.1f} kWh")

                            with col3:
                                st.metric("総売電量", f"{total_export:,.1f} kWh")

                except Exception as e:
                    st.error(f"エラー: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())

# ===== 結果分析ページ =====
elif page == "結果分析":
    st.header("📈 結果分析")

    # 最新のシミュレーション結果を表示
    if 'latest_simulation' not in st.session_state:
        st.info("シミュレーション結果がありません。「シミュレーション実行」ページでシミュレーションを実行してください。")
    else:
        sim_data = st.session_state.latest_simulation
        results_df = sim_data['results']
        use_battery = sim_data['use_battery']

        st.subheader(f"シミュレーション: {sim_data['name']}")

        # サマリー
        st.subheader("📊 サマリー")

        total_revenue = results_df['revenue_yen'].sum()
        total_generation = results_df['pv_generation_kwh'].sum()
        total_export = results_df['export_kwh'].sum()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("総売上", f"¥{total_revenue:,.0f}")

        with col2:
            st.metric("総発電量", f"{total_generation:,.1f} kWh")

        with col3:
            st.metric("総売電量", f"{total_export:,.1f} kWh")

        with col4:
            avg_price = total_revenue / total_export if total_export > 0 else 0
            st.metric("平均売電単価", f"¥{avg_price:.2f}/kWh")

        if use_battery and 'battery_charge_kwh' in results_df.columns:
            col1, col2 = st.columns(2)

            with col1:
                total_charge = results_df['battery_charge_kwh'].sum()
                st.metric("総充電量", f"{total_charge:,.1f} kWh")

            with col2:
                total_discharge = results_df['battery_discharge_kwh'].sum()
                st.metric("総放電量", f"{total_discharge:,.1f} kWh")

        # 可視化
        tab1, tab2, tab3, tab4 = st.tabs(["発電量と価格", "蓄電池挙動", "売上分析", "データ"])

        with tab1:
            st.subheader("太陽光発電量と市場価格")

            # データ準備
            if 'market_price_yen_per_kwh' not in results_df.columns:
                results_df['market_price_yen_per_kwh'] = results_df.get('area_price_yen_per_kwh', 0)

            fig = visualization.plot_pv_and_price(results_df)
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            if use_battery and 'battery_charge_kwh' in results_df.columns:
                st.subheader("蓄電池挙動")

                fig = visualization.plot_battery_behavior(results_df)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("蓄電池を使用していません")

        with tab3:
            st.subheader("売上分析")

            # 日別売上
            daily_summary = revenue.calculate_daily_summary(results_df)
            fig = visualization.plot_daily_revenue(daily_summary)
            st.plotly_chart(fig, use_container_width=True)

            # 月別売上
            monthly_summary = revenue.calculate_monthly_summary(results_df)
            if len(monthly_summary) > 1:
                fig = visualization.plot_monthly_revenue(monthly_summary)
                st.plotly_chart(fig, use_container_width=True)

            # 時間帯別売上
            hourly_summary = revenue.calculate_hourly_summary(results_df)
            fig = visualization.plot_hourly_revenue(hourly_summary)
            st.plotly_chart(fig, use_container_width=True)

        with tab4:
            st.subheader("シミュレーション結果データ")

            st.dataframe(results_df)

            # CSVダウンロード
            csv = results_df.to_csv(index=False)
            st.download_button(
                label="CSVダウンロード",
                data=csv,
                file_name=f"{sim_data['name']}_results.csv",
                mime="text/csv"
            )

# フッター
st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.info("""
このアプリは低圧太陽光発電所とDCリンク蓄電池のJEPX売上シミュレーター（MVP版）です。

**注意**: 本アプリの計算結果は参考値であり、実際の売上を保証するものではありません。
""")

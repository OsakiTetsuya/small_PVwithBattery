"""蓄電池シミュレーションモジュール"""
import pandas as pd
import numpy as np
from typing import Dict, List


class BatterySimulator:
    """DCリンク蓄電池シミュレーター"""

    def __init__(self, config: Dict):
        """
        Parameters:
        -----------
        config : Dict
            蓄電池パラメータ
            - battery_capacity_kwh: 蓄電池容量 [kWh]
            - max_charge_kw: 最大充電出力 [kW]
            - max_discharge_kw: 最大放電出力 [kW]
            - charge_efficiency: 充電効率 [0-1]
            - discharge_efficiency: 放電効率 [0-1]
            - initial_soc_percent: 初期SOC [%]
            - min_soc_percent: 最小SOC [%]
            - max_soc_percent: 最大SOC [%]
            - pcs_capacity_kw: PCS容量 [kW]
            - grid_export_limit_kw: 系統売電上限 [kW]
            - operation_mode: 運転モード
        """
        self.capacity = config['battery_capacity_kwh']
        self.max_charge_kw = config['max_charge_kw']
        self.max_discharge_kw = config['max_discharge_kw']
        self.charge_eff = config['charge_efficiency']
        self.discharge_eff = config['discharge_efficiency']
        self.initial_soc = config['initial_soc_percent'] / 100.0 * self.capacity
        self.min_soc = config['min_soc_percent'] / 100.0 * self.capacity
        self.max_soc = config['max_soc_percent'] / 100.0 * self.capacity
        self.pcs_capacity_kw = config['pcs_capacity_kw']
        self.grid_export_limit_kw = config['grid_export_limit_kw']
        self.operation_mode = config.get('operation_mode', 'price_optimized')

        # 30分あたりの最大充放電量
        self.max_charge_30min = self.max_charge_kw * 0.5
        self.max_discharge_30min = self.max_discharge_kw * 0.5
        self.grid_export_limit_30min = self.grid_export_limit_kw * 0.5
        self.pcs_limit_30min = self.pcs_capacity_kw * 0.5

    def simulate_day(
        self,
        pv_generation: pd.Series,
        prices: pd.Series,
        discharge_slots: List[int],
        initial_soc: float = None
    ) -> Dict[int, Dict]:
        """
        1日分の蓄電池運転をシミュレーション

        Parameters:
        -----------
        pv_generation : pd.Series
            30分ごとの太陽光発電量 [kWh] (index: slot 0-47)
        prices : pd.Series
            30分ごとの市場価格 [円/kWh] (index: slot 0-47)
        discharge_slots : List[int]
            放電対象スロット番号のリスト
        initial_soc : float
            初期SOC [kWh] (Noneの場合はself.initial_socを使用)

        Returns:
        --------
        Dict[int, Dict]
            各スロットの結果
            {
                slot: {
                    'pv_generation_kwh': float,
                    'battery_charge_kwh': float,
                    'battery_discharge_kwh': float,
                    'battery_soc_kwh': float,
                    'export_kwh': float,
                    'revenue_yen': float
                }
            }
        """
        if initial_soc is None:
            soc = self.initial_soc
        else:
            soc = initial_soc

        results = {}

        for slot in range(48):
            pv_gen = pv_generation.get(slot, 0.0)
            price = prices.get(slot, 0.0)

            charge = 0.0
            discharge = 0.0

            if slot in discharge_slots:
                # 放電モード
                # 放電可能量を計算
                available_discharge = min(
                    self.max_discharge_30min,
                    (soc - self.min_soc) * self.discharge_eff
                )
                discharge = max(0, available_discharge)

                # SOCを更新
                soc -= discharge / self.discharge_eff

            else:
                # 充電モード（太陽光発電から）
                # 充電可能量を計算
                available_capacity = self.max_soc - soc
                max_charge_possible = min(
                    self.max_charge_30min * self.charge_eff,
                    available_capacity
                )

                # 充電量を決定（太陽光発電の余剰分から）
                # まずは売電上限を超える分を充電
                export_before_charge = pv_gen
                if export_before_charge > self.grid_export_limit_30min:
                    excess = export_before_charge - self.grid_export_limit_30min
                    charge = min(excess, max_charge_possible)
                else:
                    # 売電上限を超えていない場合でも、将来の高価格に備えて充電
                    # 太陽光発電の一部を充電（最大30%程度）
                    charge = min(pv_gen * 0.3, max_charge_possible)

                # SOCを更新
                soc += charge

            # 売電量を計算
            export = pv_gen - charge + discharge
            export = min(export, self.grid_export_limit_30min)
            export = min(export, self.pcs_limit_30min)
            export = max(export, 0.0)

            # 売上を計算
            revenue = export * price

            # SOCの範囲チェック
            soc = max(self.min_soc, min(soc, self.max_soc))

            results[slot] = {
                'pv_generation_kwh': pv_gen,
                'battery_charge_kwh': charge,
                'battery_discharge_kwh': discharge,
                'battery_soc_kwh': soc,
                'export_kwh': export,
                'revenue_yen': revenue
            }

        return results

    def determine_discharge_slots_top_price(
        self,
        prices: pd.Series,
        num_slots: int = None
    ) -> List[int]:
        """
        上位価格コマ方式で放電スロットを決定

        Parameters:
        -----------
        prices : pd.Series
            30分ごとの市場価格 [円/kWh] (index: slot 0-47)
        num_slots : int
            放電スロット数（Noneの場合は蓄電池容量から自動計算）

        Returns:
        --------
        List[int]
            放電対象スロット番号のリスト
        """
        if num_slots is None:
            # 蓄電池容量と最大放電出力から放電可能コマ数を計算
            num_slots = int(self.capacity / self.max_discharge_30min)
            num_slots = min(num_slots, 48)  # 最大48コマ

        # 価格が高い順にソート
        sorted_prices = prices.sort_values(ascending=False)

        # 上位num_slots個のスロットを選択
        discharge_slots = sorted_prices.head(num_slots).index.tolist()

        return discharge_slots

    def determine_discharge_slots_threshold(
        self,
        prices: pd.Series,
        threshold_yen_per_kwh: float
    ) -> List[int]:
        """
        価格しきい値方式で放電スロットを決定

        Parameters:
        -----------
        prices : pd.Series
            30分ごとの市場価格 [円/kWh] (index: slot 0-47)
        threshold_yen_per_kwh : float
            放電価格しきい値 [円/kWh]

        Returns:
        --------
        List[int]
            放電対象スロット番号のリスト
        """
        discharge_slots = prices[prices >= threshold_yen_per_kwh].index.tolist()
        return discharge_slots

    def simulate_period(
        self,
        pv_df: pd.DataFrame,
        prices_df: pd.DataFrame,
        discharge_mode: str = 'top_price',
        threshold: float = None,
        num_discharge_slots: int = None
    ) -> pd.DataFrame:
        """
        期間全体の蓄電池運転をシミュレーション

        Parameters:
        -----------
        pv_df : pd.DataFrame
            columns: ['datetime', 'generation_kwh']
        prices_df : pd.DataFrame
            columns: ['datetime', 'area_price_yen_per_kwh']
        discharge_mode : str
            'top_price' or 'threshold'
        threshold : float
            価格しきい値（threshold mode時）
        num_discharge_slots : int
            放電スロット数（top_price mode時）

        Returns:
        --------
        pd.DataFrame
            シミュレーション結果
        """
        pv_df = pv_df.copy()
        prices_df = prices_df.copy()

        pv_df['datetime'] = pd.to_datetime(pv_df['datetime'])
        prices_df['datetime'] = pd.to_datetime(prices_df['datetime'])

        pv_df['date'] = pv_df['datetime'].dt.date
        prices_df['date'] = prices_df['datetime'].dt.date

        results_list = []
        current_soc = self.initial_soc

        # 日ごとにシミュレーション
        for date in sorted(pv_df['date'].unique()):
            daily_pv = pv_df[pv_df['date'] == date].copy()
            daily_prices = prices_df[prices_df['date'] == date].copy()

            if len(daily_pv) == 0 or len(daily_prices) == 0:
                continue

            # スロット番号を割り当て
            daily_pv['slot'] = range(len(daily_pv))
            daily_prices['slot'] = range(len(daily_prices))

            pv_series = daily_pv.set_index('slot')['generation_kwh']
            price_series = daily_prices.set_index('slot')['area_price_yen_per_kwh']

            # 放電スロットを決定
            if discharge_mode == 'top_price':
                discharge_slots = self.determine_discharge_slots_top_price(
                    price_series, num_discharge_slots
                )
            else:  # threshold
                discharge_slots = self.determine_discharge_slots_threshold(
                    price_series, threshold
                )

            # 1日分をシミュレーション
            daily_results = self.simulate_day(
                pv_series, price_series, discharge_slots, current_soc
            )

            # 結果を格納
            for slot, result in daily_results.items():
                dt = daily_pv[daily_pv['slot'] == slot]['datetime'].iloc[0]
                price = daily_prices[daily_prices['slot'] == slot]['area_price_yen_per_kwh'].iloc[0]

                results_list.append({
                    'datetime': dt,
                    'market_price_yen_per_kwh': price,
                    'pv_generation_kwh': result['pv_generation_kwh'],
                    'battery_charge_kwh': result['battery_charge_kwh'],
                    'battery_discharge_kwh': result['battery_discharge_kwh'],
                    'battery_soc_kwh': result['battery_soc_kwh'],
                    'export_kwh': result['export_kwh'],
                    'revenue_yen': result['revenue_yen']
                })

            # 翌日の初期SOCを更新
            if len(daily_results) > 0:
                current_soc = daily_results[max(daily_results.keys())]['battery_soc_kwh']

        return pd.DataFrame(results_list)

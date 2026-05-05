"""可視化モジュール"""
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import Optional


def plot_pv_and_price(df: pd.DataFrame) -> go.Figure:
    """
    太陽光発電量と市場価格を可視化

    Parameters:
    -----------
    df : pd.DataFrame
        columns: ['datetime', 'pv_generation_kwh', 'export_kwh',
                  'market_price_yen_per_kwh']
    """
    fig = make_subplots(
        rows=1, cols=1,
        specs=[[{"secondary_y": True}]]
    )

    # 太陽光発電量
    fig.add_trace(
        go.Scatter(
            x=df['datetime'],
            y=df['pv_generation_kwh'],
            name='太陽光発電量',
            mode='lines',
            line=dict(color='orange', width=2)
        ),
        secondary_y=False
    )

    # 売電量
    fig.add_trace(
        go.Scatter(
            x=df['datetime'],
            y=df['export_kwh'],
            name='売電量',
            mode='lines',
            line=dict(color='green', width=2)
        ),
        secondary_y=False
    )

    # 市場価格
    fig.add_trace(
        go.Scatter(
            x=df['datetime'],
            y=df['market_price_yen_per_kwh'],
            name='JEPXエリアプライス',
            mode='lines',
            line=dict(color='blue', width=1)
        ),
        secondary_y=True
    )

    fig.update_xaxes(title_text="日時")
    fig.update_yaxes(title_text="発電量・売電量 [kWh]", secondary_y=False)
    fig.update_yaxes(title_text="価格 [円/kWh]", secondary_y=True)

    fig.update_layout(
        title="太陽光発電量と市場価格",
        hovermode='x unified',
        height=500
    )

    return fig


def plot_battery_behavior(df: pd.DataFrame) -> go.Figure:
    """
    蓄電池挙動を可視化

    Parameters:
    -----------
    df : pd.DataFrame
        columns: ['datetime', 'battery_charge_kwh', 'battery_discharge_kwh',
                  'battery_soc_kwh', 'export_kwh']
    """
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('充放電量', 'SOCと売電量'),
        vertical_spacing=0.15
    )

    # 充電量
    fig.add_trace(
        go.Bar(
            x=df['datetime'],
            y=df['battery_charge_kwh'],
            name='充電量',
            marker_color='lightblue'
        ),
        row=1, col=1
    )

    # 放電量
    fig.add_trace(
        go.Bar(
            x=df['datetime'],
            y=-df['battery_discharge_kwh'],
            name='放電量',
            marker_color='lightcoral'
        ),
        row=1, col=1
    )

    # SOC
    fig.add_trace(
        go.Scatter(
            x=df['datetime'],
            y=df['battery_soc_kwh'],
            name='SOC',
            mode='lines',
            line=dict(color='purple', width=2)
        ),
        row=2, col=1
    )

    # 売電量
    fig.add_trace(
        go.Scatter(
            x=df['datetime'],
            y=df['export_kwh'],
            name='売電量',
            mode='lines',
            line=dict(color='green', width=2)
        ),
        row=2, col=1
    )

    fig.update_xaxes(title_text="日時", row=2, col=1)
    fig.update_yaxes(title_text="kWh", row=1, col=1)
    fig.update_yaxes(title_text="kWh", row=2, col=1)

    fig.update_layout(
        title="蓄電池挙動",
        hovermode='x unified',
        height=700
    )

    return fig


def plot_daily_revenue(df: pd.DataFrame) -> go.Figure:
    """
    日別売上を可視化

    Parameters:
    -----------
    df : pd.DataFrame
        columns: ['date', 'revenue_yen']
    """
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=df['date'],
            y=df['revenue_yen'],
            name='日別売上',
            marker_color='lightgreen'
        )
    )

    fig.update_layout(
        title="日別売上",
        xaxis_title="日付",
        yaxis_title="売上 [円]",
        hovermode='x',
        height=400
    )

    return fig


def plot_monthly_revenue(df: pd.DataFrame) -> go.Figure:
    """
    月別売上を可視化

    Parameters:
    -----------
    df : pd.DataFrame
        columns: ['month', 'revenue_yen']
    """
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=df['month'],
            y=df['revenue_yen'],
            name='月別売上',
            marker_color='lightblue'
        )
    )

    fig.update_layout(
        title="月別売上",
        xaxis_title="月",
        yaxis_title="売上 [円]",
        hovermode='x',
        height=400
    )

    return fig


def plot_hourly_revenue(df: pd.DataFrame) -> go.Figure:
    """
    時間帯別売上を可視化

    Parameters:
    -----------
    df : pd.DataFrame
        columns: ['hour', 'revenue_yen']
    """
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=df['hour'],
            y=df['revenue_yen'],
            name='時間帯別売上',
            marker_color='lightyellow'
        )
    )

    fig.update_layout(
        title="時間帯別売上",
        xaxis_title="時刻",
        yaxis_title="売上 [円]",
        hovermode='x',
        height=400
    )

    return fig


def plot_price_distribution(df: pd.DataFrame) -> go.Figure:
    """
    価格帯別売電量を可視化

    Parameters:
    -----------
    df : pd.DataFrame
        columns: ['market_price_yen_per_kwh', 'export_kwh']
    """
    # 価格帯を作成
    df = df.copy()
    df['price_bin'] = pd.cut(
        df['market_price_yen_per_kwh'],
        bins=10,
        labels=[f"{i*2}-{(i+1)*2}" for i in range(10)]
    )

    binned = df.groupby('price_bin', observed=True)['export_kwh'].sum().reset_index()

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=binned['price_bin'].astype(str),
            y=binned['export_kwh'],
            name='価格帯別売電量',
            marker_color='lightcoral'
        )
    )

    fig.update_layout(
        title="価格帯別売電量",
        xaxis_title="価格帯 [円/kWh]",
        yaxis_title="売電量 [kWh]",
        hovermode='x',
        height=400
    )

    return fig


def plot_comparison_with_without_battery(
    df_with: pd.DataFrame,
    df_without: pd.DataFrame
) -> go.Figure:
    """
    蓄電池あり/なし比較を可視化

    Parameters:
    -----------
    df_with : pd.DataFrame
        蓄電池ありの結果
    df_without : pd.DataFrame
        蓄電池なしの結果
    """
    df_with = df_with.copy()
    df_without = df_without.copy()

    df_with['datetime'] = pd.to_datetime(df_with['datetime'])
    df_without['datetime'] = pd.to_datetime(df_without['datetime'])

    df_with['date'] = df_with['datetime'].dt.date
    df_without['date'] = df_without['datetime'].dt.date

    daily_with = df_with.groupby('date')['revenue_yen'].sum().reset_index()
    daily_without = df_without.groupby('date')['revenue_yen'].sum().reset_index()

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=daily_with['date'],
            y=daily_with['revenue_yen'],
            name='蓄電池あり',
            marker_color='lightblue'
        )
    )

    fig.add_trace(
        go.Bar(
            x=daily_without['date'],
            y=daily_without['revenue_yen'],
            name='蓄電池なし',
            marker_color='lightgray'
        )
    )

    fig.update_layout(
        title="蓄電池あり/なし比較（日別売上）",
        xaxis_title="日付",
        yaxis_title="売上 [円]",
        barmode='group',
        hovermode='x',
        height=500
    )

    return fig


def plot_area_generation(df: pd.DataFrame) -> go.Figure:
    """
    エリア需給・電源構成を可視化

    Parameters:
    -----------
    df : pd.DataFrame
        columns: ['datetime', 'source_type', 'generation_kwh', 'area_price_yen_per_kwh']
    """
    fig = make_subplots(
        rows=1, cols=1,
        specs=[[{"secondary_y": True}]]
    )

    # 電源種別ごとにプロット
    for source_type in df['source_type'].unique():
        source_df = df[df['source_type'] == source_type]

        fig.add_trace(
            go.Scatter(
                x=source_df['datetime'],
                y=source_df['generation_kwh'],
                name=source_type,
                mode='lines',
                stackgroup='one'
            ),
            secondary_y=False
        )

    # 市場価格
    if 'area_price_yen_per_kwh' in df.columns:
        price_df = df.drop_duplicates('datetime')
        fig.add_trace(
            go.Scatter(
                x=price_df['datetime'],
                y=price_df['area_price_yen_per_kwh'],
                name='JEPX価格',
                mode='lines',
                line=dict(color='black', width=2, dash='dash')
            ),
            secondary_y=True
        )

    fig.update_xaxes(title_text="日時")
    fig.update_yaxes(title_text="発電量 [kWh]", secondary_y=False)
    fig.update_yaxes(title_text="価格 [円/kWh]", secondary_y=True)

    fig.update_layout(
        title="エリア需給・電源構成",
        hovermode='x unified',
        height=600
    )

    return fig

#!/bin/bash

# JEPX売上シミュレーター起動スクリプト

echo "=========================================="
echo "JEPX売上シミュレーター"
echo "=========================================="
echo ""

# Python3が利用可能かチェック
if ! command -v python3 &> /dev/null
then
    echo "エラー: Python3がインストールされていません"
    exit 1
fi

# 依存パッケージをインストール
echo "依存パッケージをインストール中..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "エラー: パッケージのインストールに失敗しました"
    exit 1
fi

echo ""
echo "アプリを起動しています..."
echo "ブラウザが自動的に開きます（通常は http://localhost:8501）"
echo ""
echo "終了するには Ctrl+C を押してください"
echo ""

# Streamlitアプリを起動
streamlit run app.py

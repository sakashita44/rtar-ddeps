#!/bin/bash

# DVCのセットアップスクリプト
# このスクリプトは、DVCの初期化とリモートリポジトリの設定を行います。
# 使用方法: ./dvc_setup.sh
# 注意: このスクリプトは、DVCがインストールされていることを前提としています。
# スクリプトのエラーハンドリング
set -e  # エラーが発生した場合、スクリプトを終了します。
set -u  # 未定義の変数を使用した場合、エラーを出します。
set -o pipefail  # パイプのエラーをキャッチします。
set -x  # 実行されるコマンドを表示します。
# スクリプトの説明
echo "DVCのセットアップを開始します..."
# 必要なコマンドがインストールされているか確認
if ! command -v git &> /dev/null; then
    echo "Error: gitコマンドが見つかりません。Gitをインストールしてください。"
    echo "インストール方法: sudo apt install git (Debian系) または brew install git (macOS)"
    exit 1
fi
if ! command -v python3 &> /dev/null; then
    echo "Error: python3コマンドが見つかりません。Pythonをインストールしてください。"
    echo "インストール方法: sudo apt install python3 (Debian系) または brew install python (macOS)"
    exit 1
fi
if ! command -v pip &> /dev/null; then
    echo "Error: pipコマンドが見つかりません。pipをインストールしてください。"
    echo "インストール方法: sudo apt install python3-pip (Debian系) または brew install pip (macOS)"
    exit 1
fi
# dvcコマンドがインストールされているか確認
if ! command -v dvc &> /dev/null; then
    echo "Error: dvcコマンドが見つかりません。DVCをインストールしてください。"
    echo "インストール方法: pip install dvc (pythonが必要)"
    exit 1
fi

# 必要なディレクトリが存在しない場合は作成
mkdir -p data/dvc_repo

# DVC設定ファイルのパス
DVC_CONFIG_PATH="env/dvc.json"

# DVC設定ファイルが存在するか確認
if [ ! -f "$DVC_CONFIG_PATH" ]; then
    echo "Error: DVC設定ファイル($DVC_CONFIG_PATH)が見つかりません。"
    exit 1
fi

# DVC設定ファイルからリモート情報を読み取る
REMOTE_URL=$(grep -o '"url": "[^"]*"' "$DVC_CONFIG_PATH" | cut -d'"' -f4)
REMOTE_NAME=$(grep -o '"name": "[^"]*"' "$DVC_CONFIG_PATH" | cut -d'"' -f4)

if [ -z "$REMOTE_URL" ] || [ -z "$REMOTE_NAME" ]; then
    echo "Error: DVC設定ファイルからリモート情報を読み取れませんでした。"
    exit 1
fi

echo "DVCリモートリポジトリを設定します：$REMOTE_NAME -> $REMOTE_URL"

# DVCの初期化（既に初期化されている場合はスキップ）
if [ ! -d ".dvc" ]; then
    echo "DVCを初期化します..."
    dvc init
    echo "初期化完了。"
else
    echo "DVCは既に初期化されています。"
fi

# リモートの設定
echo "DVCリモートを設定: $REMOTE_NAME -> $REMOTE_URL"
dvc remote remove "$REMOTE_NAME" 2>/dev/null || true  # 既存の設定を削除
dvc remote add -d "$REMOTE_NAME" "$REMOTE_URL"

echo "DVC設定が完了しました。"

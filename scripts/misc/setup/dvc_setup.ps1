# DVCの初期化とリモート設定を行うPowerShellスクリプト
# 使用方法: PowerShellでこのスクリプトを実行します。
# 例: .\dvc_setup.ps1
# 注意: このスクリプトは、DVCがインストールされていることを前提としています。
# 依存関係: DVCが必要です。Pythonとpipがインストールされていることを確認してください。

# dvcコマンドがインストールされているか確認
if (-not (Get-Command dvc -ErrorAction SilentlyContinue)) {
    Write-Error "Error: dvcコマンドが見つかりません。DVCをインストールしてください。"
    Write-Host "DVCのインストール方法: pip install dvc (pythonが必要です)"
    exit 1
}

# 必要なディレクトリが存在しない場合は作成
if (-not (Test-Path "data/dvc_repo")) {
    New-Item -ItemType Directory -Path "data/dvc_repo" -Force
}

# DVC設定ファイルのパス
$DvcConfigPath = "env/dvc.json"

# DVC設定ファイルが存在するか確認
if (-not (Test-Path $DvcConfigPath)) {
    Write-Error "Error: DVC設定ファイル($DvcConfigPath)が見つかりません。"
    exit 1
}

# DVC設定ファイルからリモート情報を読み取る
$DvcConfig = Get-Content $DvcConfigPath | ConvertFrom-Json
$RemoteUrl = $DvcConfig.remote.url
$RemoteName = $DvcConfig.remote.name

if ([string]::IsNullOrEmpty($RemoteUrl) -or [string]::IsNullOrEmpty($RemoteName)) {
    Write-Error "Error: DVC設定ファイルからリモート情報を読み取れませんでした。"
    exit 1
}

Write-Host "DVCリモートリポジトリを設定します：$RemoteName -> $RemoteUrl"

# DVCの初期化（既に初期化されている場合はスキップ）
if (-not (Test-Path ".dvc")) {
    Write-Host "DVCを初期化します..."
    dvc init
    Write-Host "初期化完了。"
}
else {
    Write-Host "DVCは既に初期化されています。"
}

# リモートの設定
Write-Host "DVCリモートを設定: $RemoteName -> $RemoteUrl"
try { dvc remote remove "$RemoteName" } catch { }  # 既存の設定を削除
dvc remote add -d "$RemoteName" "$RemoteUrl"

Write-Host "DVC設定が完了しました。"

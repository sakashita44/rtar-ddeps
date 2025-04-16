# nbstripoutのセットアップスクリプト（PowerShell版）

Write-Host "Setting up nbstripout..."

# nbstripoutが実行可能か確認
try {
    & nbstripout --version | Out-Null
    Write-Host "nbstripout is installed."
}
catch {
    Write-Host "nbstripoutがインストールされていません。インストールしてください。"
    Write-Host "インストール方法: pip install nbstripout (pythonが必要です)"
    exit 1
}

# Gitの設定を行う
& git config filter.nbstripout.clean nbstripout
& git config filter.nbstripout.smudge cat
& git config filter.nbstripout.required true
& git config diff.ipynb.textconv "nbstripout -t"

# .gitattributesファイルに設定があるか確認し、なければ追加
$gitattributesFile = ".gitattributes"
$requiredSettings = @(
    "*.ipynb filter=nbstripout",
    "*.zpln filter=nbstripout",
    "*.ipynb diff=ipynb"
)

Write-Host "Checking .gitattributes file..."
if (Test-Path $gitattributesFile) {
    $gitattributesContent = Get-Content $gitattributesFile -Raw
    foreach ($setting in $requiredSettings) {
        if ($gitattributesContent -notlike "*$setting*") {
            Write-Host "Adding $setting to $gitattributesFile"
            Add-Content -Path $gitattributesFile -Value $setting
        }
        else {
            Write-Host "$setting already exists in $gitattributesFile"
        }
    }
}
else {
    Write-Host "Creating $gitattributesFile and adding required settings"
    foreach ($setting in $requiredSettings) {
        Add-Content -Path $gitattributesFile -Value $setting
    }
}

Write-Host "nbstripout setup completed successfully" -ForegroundColor Green

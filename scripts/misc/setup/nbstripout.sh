#!/bin/bash
set -e

echo "Setting up nbstripout..."

# nbstripoutがインストールされていることを確認
if ! command -v nbstripout &> /dev/null; then
    echo "nbstripoutがインストールされていません。手動でインストールしてください。"
    echo "インストール方法: pip install nbstripout (pythonが必要です)"
    exit 1
fi

# Gitの設定を行う
git config filter.nbstripout.clean nbstripout
git config filter.nbstripout.smudge cat
git config filter.nbstripout.required true
git config diff.ipynb.textconv "nbstripout -t"

# .gitattributesファイルに設定があるか確認し、なければ追加
GITATTRIBUTES_FILE=".gitattributes"
REQUIRED_SETTINGS=(
    "*.ipynb filter=nbstripout"
    "*.zpln filter=nbstripout"
    "*.ipynb diff=ipynb"
)

echo "Checking .gitattributes file..."
for setting in "${REQUIRED_SETTINGS[@]}"; do
    if ! grep -q "$setting" "$GITATTRIBUTES_FILE" 2>/dev/null; then
        echo "Adding $setting to $GITATTRIBUTES_FILE"
        echo "$setting" >> "$GITATTRIBUTES_FILE"
    else
        echo "$setting already exists in $GITATTRIBUTES_FILE"
    fi
done

echo "nbstripout setup completed successfully"

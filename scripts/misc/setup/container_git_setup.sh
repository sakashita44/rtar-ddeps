#!/bin/bash

# Git設定の更新
git config --local core.sshCommand "ssh"

# SSH設定ファイルのパス
SSH_CONFIG="/root/.ssh/config"

# 設定ファイルが存在するか確認
if [ -f "$SSH_CONFIG" ]; then
    echo "SSH設定ファイルを更新します: $SSH_CONFIG"

    # 一時ファイル作成
    TEMP_FILE=$(mktemp)

    # バックアップ作成
    cp "$SSH_CONFIG" "${SSH_CONFIG}.backup"

    # Windows形式のパスをLinux形式に変換
    # C:\Users\<username>\.ssh\<keyname> → /root/.ssh/<keyname>
    sed -E 's|IdentityFile C:\\Users\\[^\\]+\\.ssh\\([^\\]+)|IdentityFile /root/.ssh/\1|g' "$SSH_CONFIG" > "$TEMP_FILE"

    # 変換結果を元のファイルに上書き
    mv "$TEMP_FILE" "$SSH_CONFIG"

    # 権限設定
    chmod 600 "$SSH_CONFIG"

    echo "SSH設定ファイルの更新が完了しました"
    echo "変換前パス: C:\Users\<username>\.ssh\<keyname>"
    echo "変換後パス: /root/.ssh/<keyname>"
else
    echo "SSH設定ファイルが見つかりません: $SSH_CONFIG"
fi

#!/bin/bash
# 各種setupスクリプトをまとめて実行するスクリプト
# dev containerのpostCreateCommandで実行される

# スクリプトを実行する
bash ./scripts/misc/setup/dvc_setup.sh
bash ./scripts/misc/setup/nbstripout.sh
bash ./scripts/misc/setup/container_git_setup.sh

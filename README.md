# rtar-ddeps

## 概要

WIP

`rtar-ddeps` は, `rtar` フレームワークで使用されるデータ依存関係定義ファイル (`data_specifications/data_dependencies.yml`) の管理と活用を支援する Python パッケージである.
`rtar-core` のデータ解析ワークフローを補助するツール群を提供する.

[rtar-core](https://github.com/sakashita44/rtar)

## 主な機能

`rtar-ddeps` は以下の機能を提供する.

* **定義ファイルの検証 (Validation):**
    * data_dependencies.yml が所定のスキーマに準拠しているか検証する.
    * データ名や処理ステップ間の参照整合性をチェックする.
* **情報抽出 (Information Extraction):**
    * data_dependencies.yml から特定の情報 (データ一覧, 処理ステップ詳細, 依存関係など) を抽出する API や CLI を提供する.
* **ドキュメント生成 (Documentation Generation):**
    * data_dependencies.yml の内容に基づき, データフロー図 (Mermaid 形式など) やデータ定義リストなどのドキュメントを自動生成する.
* **雛形生成 (Scaffolding Generation):**
    * data_dependencies.yml に定義されたデータ項目を基に, `rtar-core` の他の仕様ファイル (`data_structure.yml`, `entity_relation.yaml`) の雛形を生成する. これにより, 仕様ファイル間の一貫性維持を支援する.
* **依存関係グラフ生成 (Dependency Graph Generation):**
    * データの依存関係を可視化するためのグラフデータ (例: Graphviz DOT 形式) を生成する.

## `rtar-core` との関係

* `rtar-ddeps` は `rtar-core` プロジェクト内に配置される data_dependencies.yml ファイルを入力として利用する.
* `rtar-ddeps` によって提供されるツールは, `rtar-core` のデータ準備, 処理, 文書化の各フェーズを支援するために設計されている.
* `rtar-ddeps` は `rtar-core` とは独立したパッケージであり, 個別にインストールおよび利用が可能である.

## data_dependencies.yml の書式

`data_dependencies.yml` の詳細な書式については、`rtar-core` プロジェクトのドキュメントを参照.
[rtar-core](https://github.com/sakashita44/rtar)

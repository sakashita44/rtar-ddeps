# rtar-ddeps

TODO
rtar-dspecにgithubリポジトリ名称が変更.
この変更への対応は現時点ではこの文章による言及のみであり，
README.mdやドキュメントの更新, またコマンドラインツール, ファイル名等の変更は行われていない.

## 概要

WIP

`rtar-ddeps` は, `rtar` フレームワークで使用されるデータ依存関係定義ファイル (`data_specifications/data_dependencies.yml`) の管理と活用を支援する Python パッケージである.
`rtar-core` のデータ解析ワークフローを補助するツール群を提供する.

[rtar-core](https://github.com/sakashita44/rtar)

## How to Use

### インストール

`pip` を使用して GitHub リポジトリから直接インストールできる.

```bash
pip install git+https://github.com/sakashita44/rtar-ddeps.git
```

開発用にローカルにクローンしてインストールする場合:

```bash
git clone https://github.com/sakashita44/rtar-ddeps.git
cd rtar-ddeps
poetry install
```

### CLI (コマンドラインインターフェース)

`rtar-ddeps` はコマンドラインから利用できるツールを提供する.

#### data_dependencies.yml の検証

`data_dependencies.yml` ファイルを検証するには, 以下のコマンドを実行する.

```bash
rtar-ddeps validate data-dependencies <ファイルパス>
```

**例:**

```bash
rtar-ddeps validate data-dependencies data_specifications/data_dependencies.yml
```

* **成功時:** コマンドは終了コード 0 で正常終了する.
* **失敗時:** エラーメッセージが出力され, コマンドは終了コード 1 で終了する.

```text
Validating data dependencies file: /path/to/your/project/data_specifications/data_dependencies.yml
Error: Schema error: expected a dictionary for dictionary value @ data['data']['intermediate_data']
Error: Required data 'raw_data_typo' is not defined in the 'data' section. @ ['data', 'intermediate_data', 'required_data']
Validation failed.
```

#### シェル補完

`rtar-ddeps` はシェル補完をサポートする. これにより, コマンドや引数の入力を `Tab` キーで補完できる.

補完を有効にするには, 使用しているシェルの設定ファイルに以下のコマンドを追加する.

* **Bash** (`~/.bashrc` または `~/.bash_profile`):

    ```bash
    eval "$(_RTAR_DDEPS_COMPLETE=bash_source rtar-ddeps)"
    ```

* **Zsh** (`~/.zshrc`):

    ```zsh
    eval "$(_RTAR_DDEPS_COMPLETE=zsh_source rtar-ddeps)"
    ```

* **Fish** (`~/.config/fish/config.fish`):

    ```fish
    _RTAR_DDEPS_COMPLETE=fish_source rtar-ddeps | source
    ```

設定ファイル変更後, シェルを再起動するか, 以下のコマンドで設定を再読み込みする.

* **Bash:** `source ~/.bashrc` または `source ~/.bash_profile`
* **Zsh:** `source ~/.zshrc`
* **Fish:** `source ~/.config/fish/config.fish`

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
[rtar-core/docs/rules/DataDependencies.md](https://github.com/sakashita44/rtar/blob/main/docs/rules/DataDependencies.md)

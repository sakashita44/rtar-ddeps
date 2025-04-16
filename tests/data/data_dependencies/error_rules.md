# data_dependencies.ymlのバリデーションルール定義

`data_dependencies.yml` 自体の記述ルールは[rtar-core/docs/rules/DataDependencies.md](https://github.com/sakashita44/rtar/blob/main/docs/rules/DataDependencies.md)を参照

## 検出対象とする異常系 (Error)

バリデーションに失敗し、修正が必要な状態と判断するケースです。

### 必須セクション/項目の不足

* トップレベルの `metadata`, `target`, `data` のいずれかが欠落している。
* `metadata` 内の `title` または `purposes` が欠落している。
* `data` 内の各データ定義において、`descriptions`, `format`, `unit` のいずれかが欠落している。
* `data` の定義で `format` が `"table"` と指定されている場合に、`columns` キー自体が欠落している。
* `data.*.columns` 内の各カラム定義において、`name` または `description` が欠落している。
* `parameter` セクションが存在する場合、その中の各パラメータ定義において `descriptions` または `unit` が欠落している。

### データ型の不一致

* YAML の各キーに対してルールで期待されるデータ型（文字列, リスト, 辞書など）と異なる型の値が指定されている。
    * 例: `target` がリストではなく文字列、`data.*.descriptions` がリストではなく文字列、など。

### 参照整合性エラー

* `target` リストに含まれるデータ名が、`data` セクションのキーとして定義されていない。
* `data.*.required_data` リストに含まれるデータ名が、`data` セクションのキーとして定義されていない。
* `data.*.required_parameter` リストに含まれるパラメータ名が、`parameter` セクションのキーとして定義されていない（`parameter` セクションが存在する場合）。
* `parameter` セクションが存在しないのに、`data.*.required_parameter` が指定されている。

### 一意性制約違反

* `data` セクション内で、同じデータ名（キー）が複数定義されている。
* `parameter` セクション内で、同じパラメータ名（キー）が複数定義されている。

### 循環参照

* `data` 間の `required_data` を辿った際に、依存関係がループしている（例: A → B → C → A）。

### 致命的な空の定義

* `target` リストが空 (`target: []`) である。
* `data` 辞書が空 (`data: {}`) である。
* `data.*.format` が `"table"` であり、かつ `columns` リストが空 (`columns: []`) である。
* `data.*.process` が指定されており、かつそのリストが空 (`process: []`) である。（処理内容が記述されていないため）

## 検出対象とする異常系 (Warning)

バリデーションは成功しますが、修正が推奨される状態と判断するケースです。

### 推奨項目が空の定義

* `metadata.purposes` リストが空 (`purposes: []`) である。（目的が不明確）
* `data.*.descriptions` リストが空 (`descriptions: []`) である。（データの説明がない）
* `data.*.required_data` が指定されており、かつそのリストが空 (`required_data: []`) である。（依存データがないのにキーが存在）
* `data.*.required_parameter` が指定されており、かつそのリストが空 (`required_parameter: []`) である。（依存パラメータがないのにキーが存在）
* `parameter.*.descriptions` リストが空 (`descriptions: []`) である（`parameter` セクションが存在する場合）。（パラメータの説明がない）
* `metadata.note` が指定されており、かつそのリストが空 (`note: []`) である。

### 想定外の `format` 文字列

* `data.*.format` に指定された文字列が、想定される推奨値（例: `"table"`, `"single"`, `"time_series"` など、事前に定義したリスト）に含まれていない。

## バリデーション対象外とするもの

* **未知のキーの存在:** ルールで定義されていないキーが存在しても、既存の必須/任意キーと名前が衝突しなければエラーや警告とはしません（ユーザー拡張のため）。
* **`format` が `"table"` でない場合の `columns` の存在:** ルール違反とはみなしません。
* **文字列内容の妥当性:** `unit`, `descriptions`, `process` などの文字列の内容が意味的に正しいかどうかのチェックは行いません。

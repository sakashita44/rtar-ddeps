# data_dependencies.ymlのバリデーションルール定義

`data_dependencies.yml` 自体の記述ルールは <https://github.com/sakashita44/rtar/blob/main/docs/rules/DataDependencies.md> を参照.

## 検出対象とする異常系 (Error)

バリデーションに失敗し, 修正が必要な状態と判断するケース.

### 必須セクション/項目の不足

* トップレベルの `metadata`, `target`, `data` のいずれかが欠落.
* `metadata` 内の `title` または `purposes` が欠落.
* `data` 内の各データ定義において, `descriptions`, `format`, `unit` のいずれかが欠落.
* `data` の定義で `format` が `"table"` と指定されている場合に, `columns` キー自体が欠落.
* `data.*.columns` 内の各カラム定義において, `name` または `description` が欠落.
* `parameter` セクションが存在する場合, その中の各パラメータ定義において `descriptions` または `unit` が欠落.

### データ型の不一致

* YAML の各キーに対してルールで期待されるデータ型 (文字列, リスト, 辞書など) と異なる型の値が指定されている.
    * 例: `target` がリストではなく文字列, `data.*.descriptions` がリストではなく文字列, `metadata.terms` がリストではなく文字列など. スキーマ定義 (`data_dependencies_schema.py`) を参照.

### 参照整合性エラー

* `target` リストに含まれるデータ名が, `data` セクションのキーとして定義されていない.
* `data.*.required_data` リストに含まれるデータ名が, `data` セクションのキーとして定義されていない.
* `data.*.required_parameter` リストに含まれるパラメータ名が, `parameter` セクションのキーとして定義されていない (`parameter` セクションが存在する場合).
* `parameter` セクションが存在しないのに, `data.*.required_parameter` が指定されている.

### 一意性制約違反

* `data` セクション内で, 同じデータ名 (キー) が複数定義されている.
* `parameter` セクション内で, 同じパラメータ名 (キー) が複数定義されている.

### 循環参照

* `data` 間の `required_data` を辿った際に, 依存関係がループしている (例: A → B → C → A).

### 致命的な空の定義

* `target` リストが空 (`target: []`).
* `data` 辞書が空 (`data: {}`).
* `data.*.format` が `"table"` であり, かつ `columns` リストが空 (`columns: []`).
* `data.*.process` が指定されており, かつそのリストが空 (`process: []`). (処理内容が記述されていないため)

### 不正な `format` 文字列

* `data.*.format` が許可される値以外の文字列.
    * 許可される値: `"table"`, `"dictionary"`, `"list"`, `"single"`, `"binary"`, `"document"`.

### 可変長データ定義エラー

* `data.*.columns` 内のカラム定義で `name` の末尾に `*` が付いている (例: `uid*`) が, アスタリスクを除いた名前 (`uid`) が `data` セクションのキーとして定義されていない.
* `data.*.columns` 内のカラム定義で `name` の末尾に `*` が付いており, 参照先のデータ (`uid`) の `format` が `"table"` であるにも関わらず, `key_source` キーがそのカラム定義内に存在しない.
* `data.*.columns` 内のカラム定義で `name` の末尾に `*` が付いており, 参照先のデータ (`uid`) の `format` が `"table"` であり, かつ `key_source` が指定されているが, `key_source` で指定された列名が参照先のデータ (`uid`) の `columns` 内に存在しない.
* `data.*.columns` 内のカラム定義で `key_source` が指定されているが, `name` の末尾に `*` が付いていない.
* `data.*.columns` 内のカラム定義で `key_source` が指定されているが, 参照先のデータ (`uid`) の `format` が `"table"` 以外.

## 検出対象とする異常系 (Warning)

バリデーションは成功するが, 修正が推奨される状態と判断するケース.

### 推奨項目が空の定義

* `metadata.purposes` リストが空 (`purposes: []`). (目的が不明確)
* `metadata.terms` が指定されているが, リストが空 (`terms: []`). (用語定義がないのにキーが存在)
* `metadata.terms` 内の用語定義で `descriptions` リストが空 (`descriptions: []`). (用語の説明がない)
* `data.*.descriptions` リストが空 (`descriptions: []`). (データの説明がない)
* `data.*.required_data` が指定されており, かつそのリストが空 (`required_data: []`). (依存データがないのにキーが存在)
* `data.*.required_parameter` が指定されており, かつそのリストが空 (`required_parameter: []`). (依存パラメータがないのにキーが存在)
* `parameter.*.descriptions` リストが空 (`descriptions: []`) (`parameter` セクションが存在する場合). (パラメータの説明がない)
* `metadata.note` が指定されており, かつそのリストが空 (`note: []`).

### 不適切な可変長データ参照 (Warning)

* `data.*.columns` 内のカラム定義で `name` の末尾に `*` が付いており, 参照先のデータ (`uid`) の `format` が `"single"`, `"binary"`, `"document"` のいずれか. (これらの形式は通常, 列名の参照元として不適切)

## バリデーション対象外とするもの

* **未知のキーの存在:** ルールで定義されていないキーが存在しても, 既存の必須/任意キーと名前が衝突しなければエラーや警告とはしない (ユーザー拡張のため). スキーマ定義で `ALLOW_EXTRA` が指定されている箇所に対応.
* **`format` が `"table"` でない場合の `columns` の存在:** ルール違反とはみなさない.
* **文字列内容の妥当性:** `unit`, `descriptions`, `process` などの文字列の内容が意味的に正しいかどうかのチェックは行わない.

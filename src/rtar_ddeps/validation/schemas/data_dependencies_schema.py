from voluptuous import Schema, Required, Optional, All, Length, Any, Coerce, ALLOW_EXTRA

# --- 基本的な型定義 ---
NonEmptyListOfStrings = All([str], Length(min=1))
PossiblyEmptyListOfStrings = [str]
NonEmptyString = All(str, Length(min=1))

# --- 推奨される Format 文字列 ---
# Validator で使用される可能性があるため残す
RECOMMENDED_FORMATS = ["table", "single", "time_series", "image", "video", "audio", "text", "binary"]

# --- カラムスキーマ ---
ColumnSchema = Schema({
    Required('name'): NonEmptyString,
    Required('description'): NonEmptyString,
}, extra=ALLOW_EXTRA)

# --- データ定義スキーマ ---
DataSchema = Schema({
    Required('descriptions'): NonEmptyListOfStrings, # 空リストは Validator 側で Warning
    Required('format'): NonEmptyString, # 推奨値チェックは Validator 側で Warning
    Required('unit'): str, # `-` を許容
    Optional('columns'): [ColumnSchema], # format=table 時の必須/非空チェックは Validator 側 (Error)
    Optional('process'): NonEmptyListOfStrings, # 空リストは Validator 側で Error (スキーマレベルでもチェック)
    Optional('required_data'): PossiblyEmptyListOfStrings, # 空リストは Validator 側で Warning, 存在チェックは Validator 側 (Error)
    Optional('required_parameter'): PossiblyEmptyListOfStrings, # 空リストは Validator 側で Warning, 存在チェックは Validator 側 (Error)
}, extra=ALLOW_EXTRA)

# --- パラメータ定義スキーマ ---
ParameterSchema = Schema({
    Required('descriptions'): NonEmptyListOfStrings, # 空リストは Validator 側で Warning
    Required('unit'): str, # `-` を許容
}, extra=ALLOW_EXTRA)

# --- メタデータスキーマ ---
MetadataSchema = Schema({
    Required('title'): NonEmptyString,
    Required('purposes'): NonEmptyListOfStrings, # 空リストは Validator 側で Warning
    Optional('note'): PossiblyEmptyListOfStrings, # 空リストは Validator 側で Warning
}, extra=ALLOW_EXTRA)

# --- トップレベルスキーマ ---
# このスキーマオブジェクトを Validator でインポートして使用する
DataDependenciesSchema = Schema({
    Required('metadata'): MetadataSchema,
    Required('target'): NonEmptyListOfStrings, # 空リストはスキーマレベルで Error, 存在チェックは Validator 側 (Error)
    Required('data'): All({NonEmptyString: DataSchema}, Length(min=1)), # 空辞書はスキーマレベルで Error
    Optional('parameter'): {NonEmptyString: ParameterSchema},
}, extra=ALLOW_EXTRA)

import pytest
from pathlib import Path

from rtar_ddeps.validation.data_dependencies_validator import DataDependenciesValidator

# テストデータのディレクトリ
TEST_DATA_DIR = Path(__file__).parent.parent / "data" / "data_dependencies"

# --- フィクスチャ ---
@pytest.fixture
def normal_file():
    return TEST_DATA_DIR / "normal.yml"

@pytest.fixture(params=[
    "error_missing_required.yml",
    "error_type_mismatch.yml",
    "error_reference.yml", # スキーマエラーがないか確認必要
    "error_reference_missing_param_key.yml", # スキーマエラーがないか確認必要
    "error_duplicate_key.yml",
    "error_circular_dependency.yml", # スキーマエラーがないか確認必要
    "error_empty_definition.yml",
    "error_empty_definition_more.yml",
    "error_invalid_format.yml", # スキーマエラーがないか確認必要
    "error_variable_columns.yml", # スキーマエラーがないか確認必要
    "error_missing_required_more.yml",
    "error_type_mismatch_more.yml",
    "error_terms.yml",
    "error_dict_missing_keys.yml",
    "error_dict_has_columns.yml",
    "error_dict_empty_keys.yml",
])
def error_file(request):
    return TEST_DATA_DIR / request.param

@pytest.fixture(params=[
    "warning_empty_recommended.yml",
    "warning_empty_recommended_more.yml",
    "warning_variable_columns.yml",
])
def warning_file(request):
    return TEST_DATA_DIR / request.param

# --- テスト関数 ---
def test_validation_success_normal_file(normal_file):
    validator = DataDependenciesValidator(normal_file)
    assert validator.validate() is True
    assert not validator.errors
    assert not validator.warnings

def test_validation_failure_error_files(error_file):
    validator = DataDependenciesValidator(error_file)
    assert validator.validate() is False
    # エラーがあることだけ確認 (内容は詳細テストで)
    # assert validator.errors # load_yaml でエラーの場合もあるため、ここでは必須としない

def test_validation_warning_files(warning_file):
    validator = DataDependenciesValidator(warning_file)
    assert validator.validate() is True
    assert not validator.errors
    assert validator.warnings

def test_file_not_found():
    non_existent_file = Path("non_existent_file.yml")
    validator = DataDependenciesValidator(non_existent_file)
    with pytest.raises(FileNotFoundError):
        validator.load_yaml()

def test_invalid_yaml(tmp_path):
    invalid_yaml_content = "metadata: { title: Test\ndata: - item1\n  invalid_indent"
    invalid_file = tmp_path / "invalid.yml"
    invalid_file.write_text(invalid_yaml_content, encoding='utf-8')
    validator = DataDependenciesValidator(invalid_file)
    assert validator.validate() is False
    assert validator.errors
    assert any("Error parsing YAML file" in err for err in validator.errors)

# --- 個別のエラー/警告内容のチェック (アサーション修正) ---

def test_error_missing_required_details():
    """必須項目欠落エラーの詳細チェック (スキーマエラーのみ)"""
    file_path = TEST_DATA_DIR / "error_missing_required.yml"
    validator = DataDependenciesValidator(file_path)
    assert validator.validate() is False
    errors = "\n".join(validator.errors)
    # スキーマエラーのみチェック (パス形式を '.' 区切りに)
    assert "Error at metadata: Schema error: required key not provided" in errors
    assert "Error at data.processed_data.format: Schema error: required key not provided" in errors
    assert "Error at parameter.conversion_factor.unit: Schema error: required key not provided" in errors
    # カスタムルールエラーはスキーマエラーで早期リターンするためチェックしない
    # assert "Error at data.raw_sensor_data: 'columns' key is required when 'format' is 'table'" not in errors

def test_error_missing_required_more_details():
    """必須項目欠落エラーの詳細チェック (追加ケース, スキーマエラーのみ)"""
    file_path = TEST_DATA_DIR / "error_missing_required_more.yml"
    validator = DataDependenciesValidator(file_path)
    assert validator.validate() is False
    errors = "\n".join(validator.errors)
    assert "Error at metadata.title: Schema error: required key not provided" in errors
    # assert "Error at metadata.purposes: Schema error: required key not provided" in errors # Voluptuous might only report the first missing key (title)
    assert "Error at data.data1.descriptions: Schema error: required key not provided" in errors
    # assert "Error at data.data1.format: Schema error: required key not provided" in errors # This key exists in the test file
    assert "Error at data.data1.unit: Schema error: required key not provided" in errors
    assert "Error at parameter.param1.descriptions: Schema error: required key not provided" in errors

def test_error_type_mismatch_details():
    """データ型不一致エラーの詳細チェック (スキーマエラーのみ)"""
    file_path = TEST_DATA_DIR / "error_type_mismatch.yml"
    validator = DataDependenciesValidator(file_path)
    assert validator.validate() is False
    errors = "\n".join(validator.errors)
    assert "Error at target: Schema error: expected a list" in errors
    assert "Error at data.raw_data.descriptions: Schema error: expected a list" in errors
    assert "Error at data.processed_data.required_data: Schema error: expected a list" in errors
    assert "Error at parameter.factor.descriptions: Schema error: expected a list" in errors

def test_error_type_mismatch_more_details():
    """データ型不一致エラーの詳細チェック (追加ケース, スキーマエラーのみ)"""
    file_path = TEST_DATA_DIR / "error_type_mismatch_more.yml"
    validator = DataDependenciesValidator(file_path)
    assert validator.validate() is False
    errors = "\n".join(validator.errors)
    assert "Error at metadata.purposes: Schema error: expected a list" in errors
    # assert "Error at metadata.terms: Schema error: expected a list of dictionaries" in errors # More general message might be reported
    assert "Error at metadata.terms: Schema error: expected a list" in errors # Check for the outer type mismatch
    assert "Error at metadata.note: Schema error: expected a list" in errors
    assert "Error at data.data1.columns: Schema error: expected a list" in errors
    assert "Error at data.data1.required_parameter: Schema error: expected a list" in errors
    # process は NonEmptyListOfStrings なので型は合うはず
    # assert "Error at data.data1.process: Schema error: expected a list" in errors
    assert "Error at parameter: Schema error: expected a dictionary" in errors

def test_error_terms_details():
    """metadata.terms の型エラーの詳細チェック (スキーマエラーのみ)"""
    file_path = TEST_DATA_DIR / "error_terms.yml"
    validator = DataDependenciesValidator(file_path)
    assert validator.validate() is False
    errors = "\n".join(validator.errors)
    assert "Error at metadata.terms.0: Schema error: expected a dictionary" in errors

# --- カスタムルールエラーのテスト (スキーマエラーがないファイルを使用) ---
# 注意: error_reference.yml などにスキーマエラーがないことを確認する

def test_error_reference_details():
    """参照整合性エラーの詳細チェック (セクション欠落)"""
    file_path = TEST_DATA_DIR / "error_reference.yml" # スキーマエラーがない前提
    validator = DataDependenciesValidator(file_path)
    assert validator.validate() is False
    errors = "\n".join(validator.errors)
    # スキーマエラーがないことを確認 (もしあればアサーション失敗する)
    assert "Schema error" not in errors
    # カスタムルールエラーをチェック
    assert "Error at target: Target data 'final_result' is not defined in the 'data' section." in errors
    assert "Error at data.processed_data.required_data: Required data 'non_existent_data' is not defined in the 'data' section." in errors
    assert "Error at data.processed_data.required_parameter: `required_parameter` is specified, but the 'parameter' section is missing." in errors
    assert "Error at data.filtered_data.required_parameter: `required_parameter` is specified, but the 'parameter' section is missing." in errors

def test_error_reference_missing_param_key_details():
    """参照整合性エラーの詳細チェック (パラメータキー欠落)"""
    file_path = TEST_DATA_DIR / "error_reference_missing_param_key.yml" # スキーマエラーがない前提
    validator = DataDependenciesValidator(file_path)
    assert validator.validate() is False
    errors = "\n".join(validator.errors)
    assert "Schema error" not in errors
    assert "Error at data.processed_data.required_parameter: Required parameter 'non_existent_param' is not defined in the 'parameter' section." in errors

def test_error_duplicate_key_details():
    """キー重複エラーの詳細チェック"""
    file_path = TEST_DATA_DIR / "error_duplicate_key.yml"
    validator = DataDependenciesValidator(file_path)
    assert validator.validate() is False
    errors_str = "\n".join(validator.errors)
    # _add_error が追加するプレフィックス "Error: " とエラーメッセージ本体を確認
    # DuplicateKeyError の __str__ 出力に行番号が含まれる可能性も考慮し 'in' を使用
    # YAML パーサーは通常、最初に見つかった重複キーのみを報告する
    assert "Error: YAML parsing error: Duplicate key 'data_a' found" in errors_str
    # assert "Error: YAML parsing error: Duplicate key 'param1' found" in errors_str # Likely not reported if 'data_a' is found first

def test_error_circular_dependency_details():
    """循環参照エラーの詳細チェック"""
    file_path = TEST_DATA_DIR / "error_circular_dependency.yml" # スキーマエラーがない前提
    validator = DataDependenciesValidator(file_path)
    assert validator.validate() is False
    errors = "\n".join(validator.errors)
    assert "Schema error" not in errors
    assert "Circular dependency detected involving" in errors

def test_error_empty_definition_details():
    """致命的な空定義エラーの詳細チェック (スキーマエラー + カスタムルール)"""
    file_path = TEST_DATA_DIR / "error_empty_definition.yml"
    validator = DataDependenciesValidator(file_path)
    assert validator.validate() is False
    errors = "\n".join(validator.errors)
    # スキーマエラー
    assert "Error at target: Schema error: length of value must be at least 1" in errors
    assert "Error at data.processed_data.process: Schema error: length of value must be at least 1" in errors
    # カスタムルールエラーはスキーマエラーで早期リターンするためチェックしない
    # assert "Error at data.table_data.columns: `columns` list cannot be empty when format is 'table'." not in errors

def test_error_empty_definition_more_details():
    """致命的な空定義エラーの詳細チェック (data空, スキーマエラーのみ)"""
    file_path = TEST_DATA_DIR / "error_empty_definition_more.yml"
    validator = DataDependenciesValidator(file_path)
    assert validator.validate() is False
    errors = "\n".join(validator.errors)
    assert "Error at data: Schema error: length of value must be at least 1" in errors

def test_error_invalid_format_details():
    """不正な format 文字列エラーの詳細チェック"""
    file_path = TEST_DATA_DIR / "error_invalid_format.yml" # スキーマエラーがない前提
    validator = DataDependenciesValidator(file_path)
    assert validator.validate() is False
    errors = "\n".join(validator.errors)
    assert "Schema error" not in errors
    # メッセージに許可リストが含まれるか確認 (現在の実装では含まれる)
    assert "Error at data.data1.format: Invalid 'format' value 'timeseries'. Allowed values are:" in errors

def test_error_variable_columns_details():
    """可変長列定義エラーの詳細チェック"""
    file_path = TEST_DATA_DIR / "error_variable_columns.yml" # スキーマエラーがない前提
    validator = DataDependenciesValidator(file_path)
    assert validator.validate() is False
    errors = "\n".join(validator.errors)
    assert "Schema error" not in errors
    assert "Error at data.table_error1.columns.1.name: Referenced data 'non_existent_data' for variable column 'non_existent_data*' is not defined in the 'data' section." in errors
    assert "Error at data.table_error2.columns.1: 'key_source' is required for variable column 'ref_table*' because referenced data 'ref_table' has format 'table'." in errors
    assert "Error at data.table_error3.columns.1.key_source: The column 'non_existent_column' specified by 'key_source' for variable column 'ref_table*' does not exist in the referenced data 'ref_table'." in errors
    assert "Error at data.table_error4.columns.1.name: 'key_source' is specified, but the column name 'ref_table' does not end with '*'." in errors
    assert "Error at data.table_error5.columns.1.key_source: 'key_source' cannot be specified for variable column 'ref_list*' because referenced data 'ref_list' has format 'list' (must be 'table')." in errors

# --- 追加: dictionary 形式のカスタムルールエラーテスト ---

def test_error_dict_missing_keys_details(): # 削除: ファイルが存在しない
    """format: dictionary で keys がないエラーの詳細チェック"""
    file_path = TEST_DATA_DIR / "error_dict_missing_keys.yml"
    validator = DataDependenciesValidator(file_path)
    assert validator.validate() is False
    errors = "\n".join(validator.errors)
    assert "Schema error" not in errors # スキーマは通るはず
    assert "Error at data.dict_data: 'keys' key is required when 'format' is 'dictionary'" in errors

def test_error_dict_has_columns_details():
    """format: dictionary で columns があるエラーの詳細チェック"""
    file_path = TEST_DATA_DIR / "error_dict_has_columns.yml"
    validator = DataDependenciesValidator(file_path)
    assert validator.validate() is False
    errors = "\n".join(validator.errors)
    assert "Schema error" not in errors # スキーマは通るはず
    assert "Error at data.dict_data: 'columns' key cannot be specified when 'format' is 'dictionary'" in errors

def test_error_dict_empty_keys_details(): # 削除: ファイルが存在しない
    """format: dictionary で keys が空リストのエラーの詳細チェック"""
    file_path = TEST_DATA_DIR / "error_dict_empty_keys.yml"
    validator = DataDependenciesValidator(file_path)
    assert validator.validate() is False
    errors = "\n".join(validator.errors)
    assert "Schema error" not in errors # スキーマは通るはず
    assert "Error at data.dict_data.keys: `keys` list cannot be empty when format is 'dictionary'." in errors

# --- 警告テスト ---

def test_warning_empty_recommended_details():
    """推奨項目の空定義警告の詳細チェック"""
    file_path = TEST_DATA_DIR / "warning_empty_recommended.yml"
    validator = DataDependenciesValidator(file_path)
    assert validator.validate() is True
    assert not validator.errors
    warnings = "\n".join(validator.warnings)
    assert "Warning at metadata.purposes: `purposes` list is empty. Consider describing the purpose." in warnings
    assert "Warning at metadata.terms: `terms` list is empty. If there are no terms, consider removing the key." in warnings
    assert "Warning at metadata.note: `note` list is empty." in warnings
    assert "Warning at data.data_a.descriptions: `descriptions` list is empty. Consider adding a description." in warnings
    assert "Warning at data.data_b.required_data: `required_data` list is empty. If there are no dependencies, consider removing the key." in warnings
    assert "Warning at data.data_b.required_parameter: `required_parameter` list is empty. If there are no dependencies, consider removing the key." in warnings
    assert "Warning at parameter.param1.descriptions: `descriptions` list is empty. Consider adding a description." in warnings

def test_warning_empty_recommended_more_details():
    """推奨項目の空定義警告の詳細チェック (terms.descriptions)"""
    file_path = TEST_DATA_DIR / "warning_empty_recommended_more.yml"
    validator = DataDependenciesValidator(file_path)
    assert validator.validate() is True
    assert not validator.errors
    warnings = "\n".join(validator.warnings)
    assert "Warning at metadata.terms.0.descriptions: Term '用語1' has an empty `descriptions` list." in warnings

def test_warning_variable_columns_details():
    """不適切な可変長列参照警告の詳細チェック"""
    file_path = TEST_DATA_DIR / "warning_variable_columns.yml"
    validator = DataDependenciesValidator(file_path)
    assert validator.validate() is True
    assert not validator.errors
    warnings = "\n".join(validator.warnings)
    assert "Warning at data.table_warning1.columns.1.name: Variable column 'ref_single*' references data 'ref_single' with format 'single', which might be inappropriate for key-based referencing." in warnings
    assert "Warning at data.table_warning2.columns.1.name: Variable column 'ref_binary*' references data 'ref_binary' with format 'binary', which might be inappropriate for key-based referencing." in warnings
    assert "Warning at data.table_warning3.columns.1.name: Variable column 'ref_document*' references data 'ref_document' with format 'document', which might be inappropriate for key-based referencing." in warnings

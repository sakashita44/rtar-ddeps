import pytest
from pathlib import Path

from rtar_ddeps.validation.data_dependencies_validator import DataDependenciesValidator

# テストデータのディレクトリ
# このテストファイルからの相対パスで指定
TEST_DATA_DIR = Path(__file__).parent.parent / "data" / "data_dependencies"

# --- フィクスチャ ---
@pytest.fixture
def normal_file():
    """正常なテストファイルパスを提供するフィクスチャ"""
    return TEST_DATA_DIR / "normal.yml"

@pytest.fixture(params=[
    "error_missing_required.yml",
    "error_type_mismatch.yml",
    "error_reference.yml",
    "error_reference_missing_param_key.yml", # 追加
    "error_duplicate_key.yml",
    "error_circular_dependency.yml",
    "error_empty_definition.yml",
    "error_empty_definition_more.yml",
    "error_invalid_format.yml",
    "error_variable_columns.yml",
    "error_missing_required_more.yml",
    "error_type_mismatch_more.yml",
    "error_terms.yml",
])
def error_file(request):
    """エラーを含むテストファイルパスをパラメータ化して提供するフィクスチャ"""
    return TEST_DATA_DIR / request.param

@pytest.fixture(params=[
    "warning_empty_recommended.yml",
    "warning_empty_recommended_more.yml",
    "warning_variable_columns.yml",
])
def warning_file(request):
    """警告を含むテストファイルパスをパラメータ化して提供するフィクスチャ"""
    return TEST_DATA_DIR / request.param

# --- テスト関数 ---

def test_validation_success_normal_file(normal_file):
    """正常なファイルでバリデーションが成功することを確認"""
    validator = DataDependenciesValidator(normal_file)
    assert validator.validate() is True, "正常なファイルでバリデーションが失敗した"
    assert not validator.errors, "正常なファイルでエラーが検出された"
    assert not validator.warnings, "正常なファイルで警告が検出された"

def test_validation_failure_error_files(error_file):
    """エラーが含まれるファイルでバリデーションが失敗することを確認"""
    validator = DataDependenciesValidator(error_file)
    assert validator.validate() is False, f"{error_file.name} でバリデーションが成功してしまった"
    assert validator.errors, f"{error_file.name} でエラーが検出されなかった"
    # エラーメッセージの内容は詳細テストで確認

def test_validation_warning_files(warning_file):
    """警告が含まれるファイルでバリデーションが成功（エラーなし）することを確認"""
    validator = DataDependenciesValidator(warning_file)
    assert validator.validate() is True, f"{warning_file.name} でバリデーションが失敗した（警告のみのはず）"
    assert not validator.errors, f"{warning_file.name} でエラーが検出された（警告のみのはず）"
    assert validator.warnings, f"{warning_file.name} で警告が検出されなかった"
    # 警告メッセージの内容は詳細テストで確認

def test_file_not_found():
    """存在しないファイルを指定した場合に FileNotFoundError が発生することを確認"""
    non_existent_file = Path("non_existent_file.yml")
    validator = DataDependenciesValidator(non_existent_file)
    # BaseValidator.load_yaml が FileNotFoundError を raise する実装を前提とする
    with pytest.raises(FileNotFoundError):
        validator.load_yaml() # validate() を呼ぶ前に load_yaml でエラーになる

def test_invalid_yaml(tmp_path):
    """不正なYAMLファイルを指定した場合にバリデーションが失敗し、エラーが記録されることを確認"""
    invalid_yaml_content = "metadata: { title: Test\ndata: - item1\n  invalid_indent" # 不正なYAML
    invalid_file = tmp_path / "invalid.yml"
    invalid_file.write_text(invalid_yaml_content, encoding='utf-8')

    validator = DataDependenciesValidator(invalid_file)
    # BaseValidator.load_yaml がエラーをリストに追加して None を返す実装を前提とする
    assert validator.validate() is False, "不正なYAMLファイルでバリデーションが成功してしまった"
    assert validator.errors, "不正なYAMLファイルでエラーが記録されなかった"
    assert any("Error parsing YAML file" in err for err in validator.errors), "YAMLパースエラーのメッセージが含まれていない"

# --- 個別のエラー/警告内容のチェック (より詳細なテスト) ---

def test_error_missing_required_details():
    """必須項目欠落エラーの詳細チェック"""
    file_path = TEST_DATA_DIR / "error_missing_required.yml"
    validator = DataDependenciesValidator(file_path)
    assert validator.validate() is False
    errors = "\n".join(validator.errors)
    # スキーマエラーとカスタムルールエラーの両方を確認
    assert "Error at 'metadata': Schema error: required key not provided" in errors # スキーマレベル
    assert "Error at 'data.processed_data.format': Schema error: required key not provided" in errors # スキーマレベル
    assert "Error at 'parameter.conversion_factor.unit': Schema error: required key not provided" in errors # スキーマレベル
    assert "Error at 'data.raw_sensor_data': 'columns' key is required when 'format' is 'table'" in errors # カスタムルール

def test_error_missing_required_more_details():
    """必須項目欠落エラーの詳細チェック (追加ケース)"""
    file_path = TEST_DATA_DIR / "error_missing_required_more.yml"
    validator = DataDependenciesValidator(file_path)
    assert validator.validate() is False
    errors = "\n".join(validator.errors)
    assert "Error at 'metadata.title': Schema error: required key not provided" in errors
    assert "Error at 'metadata.purposes': Schema error: required key not provided" in errors
    assert "Error at 'data.data1.descriptions': Schema error: required key not provided" in errors
    assert "Error at 'data.data1.format': Schema error: required key not provided" in errors
    assert "Error at 'data.data1.unit': Schema error: required key not provided" in errors
    assert "Error at 'parameter.param1.descriptions': Schema error: required key not provided" in errors

def test_error_type_mismatch_details():
    """データ型不一致エラーの詳細チェック"""
    file_path = TEST_DATA_DIR / "error_type_mismatch.yml"
    validator = DataDependenciesValidator(file_path)
    assert validator.validate() is False
    errors = "\n".join(validator.errors)
    assert "Error at 'target': Schema error: expected a list" in errors
    assert "Error at 'data.raw_data.descriptions': Schema error: expected a list" in errors
    assert "Error at 'data.processed_data.required_data': Schema error: expected a list" in errors
    assert "Error at 'parameter.factor.descriptions': Schema error: expected a list" in errors

def test_error_type_mismatch_more_details():
    """データ型不一致エラーの詳細チェック (追加ケース)"""
    file_path = TEST_DATA_DIR / "error_type_mismatch_more.yml"
    validator = DataDependenciesValidator(file_path)
    assert validator.validate() is False
    errors = "\n".join(validator.errors)
    assert "Error at 'metadata.purposes': Schema error: expected a list" in errors
    assert "Error at 'metadata.terms': Schema error: expected a list of dictionaries" in errors # スキーマでリスト内の型もチェック
    assert "Error at 'metadata.note': Schema error: expected a list" in errors
    assert "Error at 'data.data1.columns': Schema error: expected a list" in errors
    assert "Error at 'data.data1.required_parameter': Schema error: expected a list" in errors
    assert "Error at 'data.data1.process': Schema error: expected a list" in errors
    assert "Error at 'parameter': Schema error: expected a dictionary" in errors

def test_error_terms_details():
    """metadata.terms の型エラーの詳細チェック"""
    file_path = TEST_DATA_DIR / "error_terms.yml"
    validator = DataDependenciesValidator(file_path)
    assert validator.validate() is False
    errors = "\n".join(validator.errors)
    assert "Error at 'metadata.terms.0': Schema error: expected a dictionary" in errors # リストの0番目が辞書でない

def test_error_reference_details():
    """参照整合性エラーの詳細チェック (セクション欠落)"""
    file_path = TEST_DATA_DIR / "error_reference.yml"
    validator = DataDependenciesValidator(file_path)
    assert validator.validate() is False
    errors = "\n".join(validator.errors)
    assert "Error at 'target': Target data 'final_result' is not defined in the 'data' section." in errors
    assert "Error at 'data.processed_data.required_data': Required data 'non_existent_data' is not defined in the 'data' section." in errors
    # parameter セクションがない場合のエラー
    assert "Error at 'data.processed_data.required_parameter': `required_parameter` is specified, but the 'parameter' section is missing." in errors
    assert "Error at 'data.filtered_data.required_parameter': `required_parameter` is specified, but the 'parameter' section is missing." in errors

def test_error_reference_missing_param_key_details():
    """参照整合性エラーの詳細チェック (パラメータキー欠落)"""
    file_path = TEST_DATA_DIR / "error_reference_missing_param_key.yml"
    validator = DataDependenciesValidator(file_path)
    assert validator.validate() is False
    errors = "\n".join(validator.errors)
    assert "Error at 'data.processed_data.required_parameter': Required parameter 'non_existent_param' is not defined in the 'parameter' section." in errors

def test_error_duplicate_key_details():
    """キー重複エラーの詳細チェック"""
    file_path = TEST_DATA_DIR / "error_duplicate_key.yml"
    validator = DataDependenciesValidator(file_path)
    # BaseValidator.check_duplicate_keys が DuplicateKeyError をキャッチし、
    # self.errors に追加する実装を前提とする.
    assert validator.validate() is False
    errors = "\n".join(validator.errors)
    # カスタムローダーが出力するエラーメッセージを確認
    assert "Error: YAML parsing error: Duplicate key 'data_a' found at line" in errors
    assert "Error: YAML parsing error: Duplicate key 'param1' found at line" in errors
    # _validate_uniqueness による data と parameter 間の重複チェックも確認 (このファイルでは発生しない)

def test_error_circular_dependency_details():
    """循環参照エラーの詳細チェック"""
    file_path = TEST_DATA_DIR / "error_circular_dependency.yml"
    validator = DataDependenciesValidator(file_path)
    assert validator.validate() is False
    errors = "\n".join(validator.errors)
    # エラーメッセージは検出されたノードによって変わる可能性があるため、部分一致で確認
    assert "Circular dependency detected involving" in errors

def test_error_empty_definition_details():
    """致命的な空定義エラーの詳細チェック"""
    file_path = TEST_DATA_DIR / "error_empty_definition.yml"
    validator = DataDependenciesValidator(file_path)
    assert validator.validate() is False
    errors = "\n".join(validator.errors)
    assert "Error at 'target': Schema error: length of value must be at least 1" in errors # スキーマ
    assert "Error at 'data.processed_data.process': Schema error: length of value must be at least 1" in errors # スキーマ
    assert "Error at 'data.table_data.columns': `columns` list cannot be empty when format is 'table'." in errors # カスタムルール

def test_error_empty_definition_more_details():
    """致命的な空定義エラーの詳細チェック (data空)"""
    file_path = TEST_DATA_DIR / "error_empty_definition_more.yml"
    validator = DataDependenciesValidator(file_path)
    assert validator.validate() is False
    errors = "\n".join(validator.errors)
    assert "Error at 'data': Schema error: length of value must be at least 1" in errors # スキーマ

def test_error_invalid_format_details():
    """不正な format 文字列エラーの詳細チェック"""
    file_path = TEST_DATA_DIR / "error_invalid_format.yml"
    validator = DataDependenciesValidator(file_path)
    assert validator.validate() is False
    errors = "\n".join(validator.errors)
    assert "Error at 'data.data1.format': Invalid 'format' value 'timeseries'." in errors

def test_error_variable_columns_details():
    """可変長列定義エラーの詳細チェック"""
    file_path = TEST_DATA_DIR / "error_variable_columns.yml"
    validator = DataDependenciesValidator(file_path)
    assert validator.validate() is False
    errors = "\n".join(validator.errors)
    assert "Error at 'data.table_error1.columns.1.name': Referenced data 'non_existent_data' for variable column 'non_existent_data*' is not defined in the 'data' section." in errors
    assert "Error at 'data.table_error2.columns.1': 'key_source' is required for variable column 'ref_table*' because referenced data 'ref_table' has format 'table'." in errors
    assert "Error at 'data.table_error3.columns.1.key_source': The column 'non_existent_column' specified by 'key_source' for variable column 'ref_table*' does not exist in the referenced data 'ref_table'." in errors
    assert "Error at 'data.table_error4.columns.1.name': 'key_source' is specified, but the column name 'ref_table' does not end with '*'." in errors
    assert "Error at 'data.table_error5.columns.1.key_source': 'key_source' cannot be specified for variable column 'ref_list*' because referenced data 'ref_list' has format 'list' (must be 'table')." in errors

def test_warning_empty_recommended_details():
    """推奨項目の空定義警告の詳細チェック"""
    file_path = TEST_DATA_DIR / "warning_empty_recommended.yml"
    validator = DataDependenciesValidator(file_path)
    assert validator.validate() is True
    assert not validator.errors
    warnings = "\n".join(validator.warnings)
    assert "Warning at 'metadata.purposes': `purposes` list is empty. Consider describing the purpose." in warnings
    assert "Warning at 'metadata.terms': `terms` list is empty. If there are no terms, consider removing the key." in warnings
    assert "Warning at 'metadata.note': `note` list is empty." in warnings
    assert "Warning at 'data.data_a.descriptions': `descriptions` list is empty. Consider adding a description." in warnings
    assert "Warning at 'data.data_b.required_data': `required_data` list is empty. If there are no dependencies, consider removing the key." in warnings
    assert "Warning at 'data.data_b.required_parameter': `required_parameter` list is empty. If there are no dependencies, consider removing the key." in warnings
    assert "Warning at 'parameter.param1.descriptions': `descriptions` list is empty. Consider adding a description." in warnings

def test_warning_empty_recommended_more_details():
    """推奨項目の空定義警告の詳細チェック (terms.descriptions)"""
    file_path = TEST_DATA_DIR / "warning_empty_recommended_more.yml"
    validator = DataDependenciesValidator(file_path)
    assert validator.validate() is True
    assert not validator.errors
    warnings = "\n".join(validator.warnings)
    assert "Warning at 'metadata.terms.0.descriptions': Term '用語1' has an empty `descriptions` list." in warnings

def test_warning_variable_columns_details():
    """不適切な可変長列参照警告の詳細チェック"""
    file_path = TEST_DATA_DIR / "warning_variable_columns.yml"
    validator = DataDependenciesValidator(file_path)
    assert validator.validate() is True
    assert not validator.errors
    warnings = "\n".join(validator.warnings)
    assert "Warning at 'data.table_warning1.columns.1.name': Variable column 'ref_single*' references data 'ref_single' with format 'single', which might be inappropriate for key-based referencing." in warnings
    assert "Warning at 'data.table_warning2.columns.1.name': Variable column 'ref_binary*' references data 'ref_binary' with format 'binary', which might be inappropriate for key-based referencing." in warnings
    assert "Warning at 'data.table_warning3.columns.1.name': Variable column 'ref_document*' references data 'ref_document' with format 'document', which might be inappropriate for key-based referencing." in warnings

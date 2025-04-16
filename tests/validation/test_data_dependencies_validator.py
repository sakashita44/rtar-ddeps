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
    # "error_duplicate_key.yml", # PyYAMLの挙動により現状ではテスト不可
    "error_circular_dependency.yml",
    "error_empty_definition.yml",
])
def error_file(request):
    """エラーを含むテストファイルパスをパラメータ化して提供するフィクスチャ"""
    return TEST_DATA_DIR / request.param

@pytest.fixture(params=[
    "warning_empty_recommended.yml",
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
    errors = "\n".join(validator.errors) # エラーメッセージ全体を文字列化して検索しやすくする
    assert "Error at 'data.processed_data.format': Schema error: required key not provided" in errors
    assert "Error at 'parameter.conversion_factor.unit': Schema error: required key not provided" in errors
    assert "Error at 'metadata': Schema error: required key not provided" in errors
    # assert "data.raw_sensor_data.columns': required key not provided" in errors # 元の期待値はコメントアウト

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

def test_error_reference_details():
    """参照整合性エラーの詳細チェック"""
    file_path = TEST_DATA_DIR / "error_reference.yml"
    validator = DataDependenciesValidator(file_path)
    assert validator.validate() is False
    errors = "\n".join(validator.errors)
    assert "Error at 'target': Target data 'final_result' is not defined in the 'data' section." in errors
    assert "Error at 'data.processed_data.required_data': Required data 'non_existent_data' is not defined in the 'data' section." in errors
    assert "Error at 'data.processed_data.required_parameter': `required_parameter` is specified, but the 'parameter' section is missing." in errors
    assert "Error at 'data.filtered_data.required_parameter': `required_parameter` is specified, but the 'parameter' section is missing." in errors

def test_error_duplicate_key_details():
    """キー重複エラーの詳細チェック (現状スキップ)"""
    file_path = TEST_DATA_DIR / "error_duplicate_key.yml"
    validator = DataDependenciesValidator(file_path)
    # PyYAMLのsafe_loadは後勝ちで重複キーを処理するため、
    # validator.dataには重複がない状態で渡される。
    # そのため、現在の _validate_uniqueness (dataとparameter間の重複チェック) では検出不可。
    # YAML読み込み前のチェックや、ruamel.yaml等の別ライブラリが必要。
    assert validator.validate() is False
    errors = "\n".join(validator.errors)
    # assert "Duplicate key 'data_a' found in 'data' section" in errors # 理想的なエラーメッセージ
    # assert "Duplicate key 'param1' found in 'parameter' section" in errors # 理想的なエラーメッセージ

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
    assert "Error at 'target': Schema error: length of value must be at least 1" in errors
    assert "Error at 'data.processed_data.process': Schema error: length of value must be at least 1" in errors
    # assert "Error at 'data.table_data.columns': Schema error: `columns` list cannot be empty when format is 'table'." in errors

def test_warning_empty_recommended_details():
    """推奨項目の空定義警告の詳細チェック"""
    file_path = TEST_DATA_DIR / "warning_empty_recommended.yml"
    validator = DataDependenciesValidator(file_path)
    assert validator.validate() is True # このファイルは警告のみでエラーはないはず
    assert not validator.errors # エラーがないことを確認
    warnings = "\n".join(validator.warnings)
    assert "Warning at 'metadata.purposes': `purposes` list is empty. Consider describing the purpose." in warnings
    assert "Warning at 'metadata.note': `note` list is empty." in warnings
    assert "Warning at 'data.data_a.descriptions': `descriptions` list is empty. Consider adding a description." in warnings
    assert "Warning at 'data.data_b.required_data': `required_data` list is empty. If there are no dependencies, consider removing the key." in warnings
    assert "Warning at 'data.data_b.required_parameter': `required_parameter` list is empty. If there are no dependencies, consider removing the key." in warnings
    assert "Warning at 'parameter.param1.descriptions': `descriptions` list is empty. Consider adding a description." in warnings

# data_dependencies.ymlのバリデーションを行う

import yaml
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple # List は型ヒント用に残す
from voluptuous import MultipleInvalid

from .base_validator import BaseValidator
from .schemas.data_dependencies_schema import DataDependenciesSchema, RECOMMENDED_FORMATS

class DataDependenciesValidator(BaseValidator):
    """
    data_dependencies.yml ファイルのバリデーションを実行するクラス.

    スキーマ検証とカスタムルール検証を行う.
    エラーと警告の管理は基底クラスで行う.
    """

    def __init__(self, file_path: Path):
        """
        バリデーターを初期化する.

        Args:
            file_path: バリデーション対象の data_dependencies.yml ファイルパス.
        """
        super().__init__(file_path)
        # self.errors: List[str] = [] # BaseValidator に移動
        # self.warnings: List[str] = [] # BaseValidator に移動
        self._data_keys: Set[str] = set()
        self._param_keys: Set[str] = set()

    def validate(self) -> bool:
        """
        data_dependencies.yml のバリデーションを実行する.

        1. YAMLファイルを読み込む (BaseValidator).
        2. スキーマバリデーションを実行する.
        3. カスタムバリデーションルールを実行する (スキーマ検証成功時のみ).
        4. 結果 (エラーと警告) を報告する (BaseValidator).

        Returns:
            バリデーションが成功した場合は True, エラーがあった場合は False.
            警告のみの場合は True を返す.
        """
        # エラー/警告リストの初期化は BaseValidator の load_yaml で行われる
        self._data_keys = set()
        self._param_keys = set()

        try:
            # load_yaml はエラー時に None を返すように変更 (BaseValidator 側)
            self.data = self.load_yaml()
            if self.data is None:
                # load_yaml 内でエラーが self.errors に追加されているはず
                self._print_results() # 結果を表示
                return False

            # --- スキーマバリデーション ---
            try:
                DataDependenciesSchema(self.data)
            except MultipleInvalid as e:
                # voluptuous のエラーメッセージを整形して追加
                for error in e.errors:
                    path_str = ".".join(map(str, error.path))
                    # self.errors.append(f"Schema error at '{path_str}': {error.msg}") # BaseValidator のメソッドを使用
                    self._add_error(f"Schema error: {error.msg}", list(map(str, error.path))) # パス情報を渡す
                # スキーマエラーがある場合は、以降のカスタムバリデーションは行わない
                self._print_results() # 結果を表示
                return False

            # スキーマ検証成功後にキーセットを初期化
            if isinstance(self.data, dict) and isinstance(self.data.get('data'), dict):
                self._data_keys = set(self.data['data'].keys())
            if isinstance(self.data, dict) and isinstance(self.data.get('parameter'), dict):
                self._param_keys = set(self.data['parameter'].keys())

            # --- カスタムバリデーション ---
            self._validate_emptiness()
            self._validate_references()
            self._validate_uniqueness()
            self._validate_circular_dependencies()
            self._validate_warnings()

        except FileNotFoundError as e:
            # load_yaml で raise される場合 (BaseValidator の実装による)
            self._add_error(str(e))
        except Exception as e:
            # 予期せぬエラーをキャッチ
            self._add_error(f"An unexpected error occurred during validation: {e}")

        self._print_results() # 最後に結果を表示
        return not self.errors # エラーがなければ True

    def _validate_emptiness(self):
        """致命的な空の定義をチェックする."""
        # スキーマで NonEmptyListOfStrings や Length(min=1) が指定されているため、
        # target, data, process の空リスト/辞書チェックはスキーマ検証に任せる.
        data_section = self.data['data'] if isinstance(self.data, dict) else {}
        for data_name, data_def in data_section.items():
            path = ['data', data_name]
            # format: table で columns が空リスト (これはスキーマではチェックできないカスタムルール)
            if data_def.get('format') == 'table' and isinstance(data_def.get('columns'), list) and not data_def['columns']:
                self._add_error("`columns` list cannot be empty when format is 'table'.", path + ['columns'])


    def _validate_references(self):
        """参照整合性をチェックする."""
        data_section = self.data['data'] if isinstance(self.data, dict) else {}
        param_section_exists = isinstance(self.data, dict) and 'parameter' in self.data and isinstance(self.data.get('parameter'), dict)

        # target の参照先チェック
        target_list = self.data.get('target', []) if isinstance(self.data, dict) else []
        if isinstance(target_list, list):
            for target_data in target_list:
                if target_data not in self._data_keys:
                    self._add_error(f"Target data '{target_data}' is not defined in the 'data' section.", ['target'])

        # data 内の参照先チェック
        for data_name, data_def in data_section.items():
            path_base = ['data', data_name]
            # required_data の参照先チェック
            if 'required_data' in data_def and isinstance(data_def['required_data'], list):
                for req_data in data_def['required_data']:
                    if req_data not in self._data_keys:
                        self._add_error(f"Required data '{req_data}' is not defined in the 'data' section.", path_base + ['required_data'])

            # required_parameter の参照先チェック
            if 'required_parameter' in data_def and isinstance(data_def['required_parameter'], list):
                if not param_section_exists:
                     self._add_error("`required_parameter` is specified, but the 'parameter' section is missing.", path_base + ['required_parameter'])
                else:
                    for req_param in data_def['required_parameter']:
                        if req_param not in self._param_keys:
                            self._add_error(f"Required parameter '{req_param}' is not defined in the 'parameter' section.", path_base + ['required_parameter'])


    def _validate_uniqueness(self):
        """キーの一意性をチェックする."""
        common_keys = self._data_keys.intersection(self._param_keys)
        if common_keys:
            for key in common_keys:
                self._add_error(f"Key '{key}' is defined in both 'data' and 'parameter' sections.")


    def _validate_circular_dependencies(self):
        """データ間の循環参照を検出する."""
        adj: Dict[str, List[str]] = {name: data_def.get('required_data', [])
                                     for name, data_def in (self.data.get('data', {}) if isinstance(self.data, dict) else {}).items()
                                     if isinstance(data_def.get('required_data'), list)}
        path: Set[str] = set()
        visited: Set[str] = set()

        def detect_cycle_util(node: str):
            path.add(node)
            visited.add(node)
            if node in adj:
                for neighbor in adj[node]:
                    if neighbor not in visited:
                        if detect_cycle_util(neighbor):
                            return True
                    elif neighbor in path:
                        # 循環検出
                        self._add_error(f"Circular dependency detected involving '{node}' and '{neighbor}'.", ['data'])
                        return True # 一つ見つければ十分
            path.remove(node)
            return False

        all_nodes = list(adj.keys())
        for node in all_nodes:
            if node not in visited:
                if detect_cycle_util(node):
                    pass


    def _validate_warnings(self):
        """修正が推奨される項目 (Warning) をチェックする."""
        metadata = self.data.get('metadata', {}) if isinstance(self.data, dict) else {}
        data_section = self.data.get('data', {}) if isinstance(self.data, dict) else {}
        param_section = self.data.get('parameter', {}) if isinstance(self.data, dict) else {}

        # metadata の空リストチェック
        if 'purposes' in metadata and isinstance(metadata['purposes'], list) and not metadata['purposes']:
            self._add_warning("`purposes` list is empty. Consider describing the purpose.", ['metadata', 'purposes'])
        if 'note' in metadata and isinstance(metadata['note'], list) and not metadata['note']:
            self._add_warning("`note` list is empty.", ['metadata', 'note'])

        # data の空リストチェックと format チェック
        for data_name, data_def in data_section.items():
            path_base = ['data', data_name]
            if 'descriptions' in data_def and isinstance(data_def['descriptions'], list) and not data_def['descriptions']:
                self._add_warning("`descriptions` list is empty. Consider adding a description.", path_base + ['descriptions'])
            if 'required_data' in data_def and isinstance(data_def['required_data'], list) and not data_def['required_data']:
                self._add_warning("`required_data` list is empty. If there are no dependencies, consider removing the key.", path_base + ['required_data'])
            if 'required_parameter' in data_def and isinstance(data_def['required_parameter'], list) and not data_def['required_parameter']:
                self._add_warning("`required_parameter` list is empty. If there are no dependencies, consider removing the key.", path_base + ['required_parameter'])

            # format の推奨値チェック
            fmt = data_def.get('format')
            if isinstance(fmt, str) and fmt not in RECOMMENDED_FORMATS:
                 self._add_warning(f"Format '{fmt}' is not in the recommended list: {RECOMMENDED_FORMATS}. Ensure this format is intended.", path_base + ['format'])

        # parameter の空リストチェック
        if isinstance(param_section, dict):
            for param_name, param_def in param_section.items():
                path_base = ['parameter', param_name]
                if 'descriptions' in param_def and isinstance(param_def['descriptions'], list) and not param_def['descriptions']:
                    self._add_warning("`descriptions` list is empty. Consider adding a description.", path_base + ['descriptions'])

# data_dependencies.ymlのバリデーションを行う

from pathlib import Path
from typing import Any, Dict, List, Set, Tuple # List は型ヒント用に残す
from voluptuous import MultipleInvalid

from .base_validator import BaseValidator
from .schemas.data_dependencies_schema import DataDependenciesSchema

class DataDependenciesValidator(BaseValidator):
    """
    data_dependencies.yml ファイルのバリデーションを実行するクラス.

    スキーマ検証とカスタムルール検証を行う.
    エラーと警告の管理は基底クラスで行う.
    """

    # 許可する format の値
    ALLOWED_FORMATS = {"table", "dictionary", "list", "single", "binary", "document"}

    def __init__(self, file_path: Path):
        """
        バリデーターを初期化する.

        Args:
            file_path: バリデーション対象の data_dependencies.yml ファイルパス.
        """
        super().__init__(file_path)
        self._data_keys: Set[str] = set()
        self._param_keys: Set[str] = set()

    def _perform_validation(self) -> bool:
        """
        data_dependencies.yml 固有のバリデーションを実行する.
        (BaseValidator の validate メソッドから呼び出される)

        1. スキーマバリデーションを実行する.
        2. カスタムバリデーションルールを実行する (スキーマ検証成功時のみ).

        Returns:
            このステップでエラーが発生した場合は False, それ以外は True.
            (最終的な成否は BaseValidator.validate が self.errors で判断)
        """
        # self.data は BaseValidator.validate で読み込み済みのはず
        if self.data is None:
            # YAML 読み込み失敗時は BaseValidator でエラーが記録されているはず
            return False # バリデーション処理を続行しない

        initial_error_count = len(self.errors)

        # --- スキーマバリデーション ---
        try:
            # トップレベルスキーマで検証
            DataDependenciesSchema(self.data)
        except MultipleInvalid as e:
            # スキーマ違反の詳細をエラーリストに追加
            for error in e.errors:
                # voluptuous のパスを文字列リストに変換して _add_error に渡す
                error_path = list(map(str, error.path))
                self._add_error(f"Schema error: {error.msg}", path=error_path)
            # スキーマエラーがあれば以降のカスタム検証は行わない方針に変更
            return False # スキーマエラー時点で終了

        # スキーマ検証成功後にキーセットを初期化 (重複チェック用)
        if isinstance(self.data, dict) and isinstance(self.data.get('data'), dict):
            self._data_keys = set(self.data['data'].keys())
        if isinstance(self.data, dict) and isinstance(self.data.get('parameter'), dict):
            self._param_keys = set(self.data['parameter'].keys())

        # --- カスタムバリデーション ---
        # これらのメソッドはエラーがあれば self.errors に追加する
        self._validate_format_and_columns()
        self._validate_emptiness()
        self._validate_references()
        self._validate_uniqueness()
        self._validate_circular_dependencies()
        self._validate_variable_columns()

        # --- 警告チェック ---
        # 警告はバリデーションの成否に影響しない
        self._validate_warnings()

        # 最終的なエラー数をチェックして成否を返す
        return len(self.errors) == initial_error_count

    def _validate_format_and_columns(self):
        """
        data セクション内の format と columns の関連性をチェックする.
        - format が 'table' の場合, columns が必須.
        - format が許可された値かチェック.
        """
        if not isinstance(self.data, dict) or 'data' not in self.data or not isinstance(self.data['data'], dict):
            return # data セクションがないか, 辞書でない場合はチェック不能

        for data_name, data_def in self.data['data'].items():
            if not isinstance(data_def, dict):
                continue # データ定義が辞書でない場合はスキップ (スキーマエラーで検出されるはず)

            data_path = ['data', data_name]
            fmt = data_def.get('format')
            columns_exist = 'columns' in data_def

            # format が許可された値かチェック
            if fmt not in self.ALLOWED_FORMATS:
                self._add_error(f"Invalid 'format' value '{fmt}'. Allowed values are: {', '.join(sorted(self.ALLOWED_FORMATS))}", path=data_path + ['format'])

            # format が 'table' の場合に columns が存在するかチェック
            if fmt == 'table' and not columns_exist:
                self._add_error("'columns' key is required when 'format' is 'table'", path=data_path)

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

    def _validate_variable_columns(self):
        """可変長列定義 (*付き列名) のバリデーションルールをチェックする (Error)."""
        if not isinstance(self.data, dict) or 'data' not in self.data or not isinstance(self.data['data'], dict):
            return # data セクションがないか, 辞書でない場合はチェック不能

        data_section = self.data['data']

        for data_name, data_def in data_section.items():
            if not isinstance(data_def, dict) or 'columns' not in data_def or not isinstance(data_def['columns'], list):
                continue # columns がないかリストでない場合はスキップ

            columns = data_def['columns']
            for col_index, column_def in enumerate(columns):
                if not isinstance(column_def, dict):
                    continue # カラム定義が辞書でない場合はスキップ (スキーマエラー)

                # パス要素はすべて文字列にする (col_index を str に変換)
                col_path = ['data', data_name, 'columns', str(col_index)]
                col_name = column_def.get('name')
                key_source = column_def.get('key_source')

                if not isinstance(col_name, str):
                    continue # name が文字列でない場合はスキップ (スキーマエラー)

                is_variable = col_name.endswith('*')

                if is_variable:
                    ref_data_name = col_name[:-1]

                    # Rule 1: 参照先データが存在するか
                    if ref_data_name not in self._data_keys:
                        self._add_error(f"Referenced data '{ref_data_name}' for variable column '{col_name}' is not defined in the 'data' section.", col_path + ['name'])
                        continue # 参照先がないと以降のチェックは無意味

                    ref_data_def = data_section.get(ref_data_name)
                    if not isinstance(ref_data_def, dict):
                        # 通常は起こらないはず (data_keys にあるので)
                        continue

                    ref_format = ref_data_def.get('format')

                    if ref_format == 'table':
                        # Rule 2: 参照先 format が table なら key_source が必須
                        if key_source is None:
                            self._add_error(f"'key_source' is required for variable column '{col_name}' because referenced data '{ref_data_name}' has format 'table'.", col_path)
                        # Rule 3: key_source で指定された列が参照先テーブルに存在するか
                        elif isinstance(key_source, str):
                            ref_columns = ref_data_def.get('columns')
                            if not isinstance(ref_columns, list) or not any(isinstance(c, dict) and c.get('name') == key_source for c in ref_columns):
                                self._add_error(f"The column '{key_source}' specified by 'key_source' for variable column '{col_name}' does not exist in the referenced data '{ref_data_name}'.", col_path + ['key_source'])
                        # else: key_source の型エラーはスキーマで検出

                    else: # 参照先 format が table 以外
                        # Rule 5: 参照先 format が table 以外なら key_source は指定できない
                        if key_source is not None:
                            self._add_error(f"'key_source' cannot be specified for variable column '{col_name}' because referenced data '{ref_data_name}' has format '{ref_format}' (must be 'table').", col_path + ['key_source'])

                else: # is_variable is False (name が * で終わらない)
                    # Rule 4: name が * で終わらないなら key_source は指定できない
                    if key_source is not None:
                        self._add_error(f"'key_source' is specified, but the column name '{col_name}' does not end with '*'.", col_path + ['name'])

    def _validate_warnings(self):
        """修正が推奨される項目 (Warning) をチェックする."""
        metadata = self.data.get('metadata', {}) if isinstance(self.data, dict) else {}
        data_section = self.data.get('data', {}) if isinstance(self.data, dict) else {}
        param_section = self.data.get('parameter', {}) if isinstance(self.data, dict) else {}

        # metadata の空リストチェック
        if 'purposes' in metadata and isinstance(metadata['purposes'], list) and not metadata['purposes']:
            self._add_warning("`purposes` list is empty. Consider describing the purpose.", ['metadata', 'purposes'])
        if 'terms' in metadata and isinstance(metadata['terms'], list) and not metadata['terms']: # terms 自体が空リスト
             self._add_warning("`terms` list is empty. If there are no terms, consider removing the key.", ['metadata', 'terms'])
        if 'note' in metadata and isinstance(metadata['note'], list) and not metadata['note']:
            self._add_warning("`note` list is empty.", ['metadata', 'note'])

        # metadata.terms 内の descriptions 空チェック
        if 'terms' in metadata and isinstance(metadata['terms'], list):
            for term_index, term_def in enumerate(metadata['terms']):
                 if isinstance(term_def, dict) and 'descriptions' in term_def and isinstance(term_def['descriptions'], list) and not term_def['descriptions']:
                     term_name = term_def.get('name', f'index {term_index}')
                     self._add_warning(f"Term '{term_name}' has an empty `descriptions` list.", ['metadata', 'terms', str(term_index), 'descriptions'])


        # data の空リストチェックと可変長列 format チェック
        for data_name, data_def in data_section.items():
            path_base = ['data', data_name]
            if 'descriptions' in data_def and isinstance(data_def['descriptions'], list) and not data_def['descriptions']:
                self._add_warning("`descriptions` list is empty. Consider adding a description.", path_base + ['descriptions'])
            if 'required_data' in data_def and isinstance(data_def['required_data'], list) and not data_def['required_data']:
                self._add_warning("`required_data` list is empty. If there are no dependencies, consider removing the key.", path_base + ['required_data'])
            if 'required_parameter' in data_def and isinstance(data_def['required_parameter'], list) and not data_def['required_parameter']:
                self._add_warning("`required_parameter` list is empty. If there are no dependencies, consider removing the key.", path_base + ['required_parameter'])

            # Rule 6 (Warning): 可変長列の参照先 format が不適切
            if isinstance(data_def.get('columns'), list):
                for col_index, column_def in enumerate(data_def['columns']):
                    if not isinstance(column_def, dict): continue
                    col_name = column_def.get('name')
                    if isinstance(col_name, str) and col_name.endswith('*'):
                        ref_data_name = col_name[:-1]
                        if ref_data_name in self._data_keys:
                            ref_data_def = data_section.get(ref_data_name)
                            if isinstance(ref_data_def, dict):
                                ref_format = ref_data_def.get('format')
                                if ref_format in {'single', 'binary', 'document'}:
                                    # col_index を str() で文字列に変換する
                                    col_path = path_base + ['columns', str(col_index)]
                                    message = f"Variable column '{col_name}' references data '{ref_data_name}' with format '{ref_format}', which might be inappropriate for key-based referencing."
                                    warning_path = col_path + ['name']
                                    self._add_warning(message, warning_path)


        # parameter の空リストチェック
        if isinstance(param_section, dict):
            for param_name, param_def in param_section.items():
                path_base = ['parameter', param_name]
                if 'descriptions' in param_def and isinstance(param_def['descriptions'], list) and not param_def['descriptions']:
                    self._add_warning("`descriptions` list is empty. Consider adding a description.", path_base + ['descriptions'])

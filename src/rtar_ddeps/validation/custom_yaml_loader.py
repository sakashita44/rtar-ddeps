# YAML 読み込み時にキーの重複を検出するカスタムローダー
import yaml
from yaml.loader import SafeLoader
from collections.abc import Mapping # Mapping 型のインポート

class DuplicateKeyError(yaml.YAMLError):
    """キー重複エラーを表すカスタム例外"""
    pass

class CustomDuplicateKeyLoader(SafeLoader):
    """YAML 読み込み時にキーの重複を検出するカスタムローダー"""

    def construct_mapping(self, node, deep=False):
        """
        マッピング (辞書) を構築する際にキーの重複をチェックする.
        """
        mapping = {}
        keys_seen = set() # このマッピング内で既出のキーを記録
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            # キーがハッシュ可能かチェック (辞書のキーとして使えるか)
            try:
                hash(key)
            except TypeError as exc:
                raise yaml.constructor.ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    f"found unhashable key: {exc}",
                    key_node.start_mark,
                ) from exc

            # キーの重複チェック
            if key in keys_seen:
                # 重複が見つかったらカスタムエラーを発生
                raise DuplicateKeyError(
                    f"Duplicate key '{key}' found at line {key_node.start_mark.line + 1}, column {key_node.start_mark.column + 1}"
                )
            keys_seen.add(key)
            value = self.construct_object(value_node, deep=deep)
            mapping[key] = value
        return mapping

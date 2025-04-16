import abc
from pathlib import Path
import yaml
from typing import List # 追加

class BaseValidator(abc.ABC):
    """
    バリデーターの基底クラス.

    共通のファイル読み込み機能, エラー/警告管理機能,
    および具象クラスで実装されるべき `validate` メソッドのインターフェースを定義する.
    """
    def __init__(self, file_path: Path):
        """
        バリデーターを初期化する.

        Args:
            file_path: バリデーション対象のファイルパス.
        """
        if not isinstance(file_path, Path):
            raise TypeError("file_path must be a Path object.")
        self.file_path = file_path
        self.data = None # 読み込んだデータを保持
        self.errors: List[str] = [] # エラーメッセージを格納するリスト
        self.warnings: List[str] = [] # 警告メッセージを格納するリスト

    def load_yaml(self) -> dict | list | None:
        """
        指定されたパスからYAMLファイルを読み込む.

        Returns:
            読み込んだデータ (辞書またはリスト), 読み込み失敗時はNone.
        Raises:
            FileNotFoundError: ファイルが存在しない場合.
            yaml.YAMLError: YAMLのパースに失敗した場合.
        """
        self.errors = [] # 読み込み前にエラーリストをクリア
        self.warnings = [] # 読み込み前に警告リストをクリア
        if not self.file_path.exists():
            # FileNotFoundError を raise する代わりにエラーリストに追加することも検討可能
            # ここでは raise する元の実装を踏襲
            raise FileNotFoundError(f"File not found: {self.file_path}")
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.data = yaml.safe_load(f)
            return self.data
        except yaml.YAMLError as e:
            self.errors.append(f"Error parsing YAML file {self.file_path}: {e}")
            # print(f"Error parsing YAML file {self.file_path}: {e}") # print は _print_results に任せる
            # raise # エラーを再送出せず、エラーリストに追加して None を返す方針に変更も可
            return None # パースエラー時は None を返し、呼び出し元でエラーリストを確認
        except Exception as e:
            self.errors.append(f"An unexpected error occurred while loading {self.file_path}: {e}")
            # print(f"An unexpected error occurred while loading {self.file_path}: {e}")
            # raise
            return None # 予期せぬエラー時も None を返す

    def _add_error(self, message: str, path: List[str] | None = None):
        """エラーメッセージをリストに追加する."""
        prefix = f"Error at '{".".join(path)}': " if path else "Error: "
        self.errors.append(prefix + message)

    def _add_warning(self, message: str, path: List[str] | None = None):
        """警告メッセージをリストに追加する."""
        prefix = f"Warning at '{".".join(path)}': " if path else "Warning: "
        self.warnings.append(prefix + message)

    def _print_results(self):
        """バリデーション結果を標準出力/エラー出力に出力する."""
        if not self.errors and not self.warnings:
            print(f"Validation successful for {self.file_path}")
        else:
            print(f"Validation finished for {self.file_path}:")
            if self.warnings:
                print("\n--- Warnings ---")
                for warning in self.warnings:
                    print(f"- {warning}")
            if self.errors:
                print("\n--- Errors ---")
                for error in self.errors:
                    print(f"- {error}")
                print("\nValidation failed.")
            else:
                # エラーがなく警告のみの場合
                print("\nValidation successful (with warnings).")

    @abc.abstractmethod
    def validate(self) -> bool:
        """
        具体的なバリデーションロジックを実行する抽象メソッド.

        具象サブクラスでこのメソッドをオーバーライドして,
        特定のファイルタイプに対するバリデーションルールを実装する必要がある.
        実装内では self._add_error や self._add_warning を使用して結果を記録し、
        最後に self._print_results() を呼び出すことが推奨される.

        Returns:
            バリデーションが成功した場合はTrue (警告のみの場合も含む),
            エラーがあった場合はFalse.
        """
        pass # 実装はサブクラスで行う

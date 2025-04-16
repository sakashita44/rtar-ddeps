import click
from pathlib import Path
# バリデータークラスをインポート (相対インポート)
from .validation.data_dependencies_validator import DataDependenciesValidator

# --- click を使ったコマンド定義 ---

# 1. メインのコマンドグループ 'cli' を定義
# @click.group() デコレータは、この関数が他のコマンド (サブコマンド) を
# まとめるグループであることを示す.
@click.group(help="RTAR Data Dependencies management tool.")
def cli():
    """RTAR データ依存関係管理ツール."""
    # この関数自体は通常、何も実行しない (pass でも可).
    # サブコマンドが呼び出されるためのエントリーポイントとなる.
    pass

# 2. 'validate' サブコマンドグループを定義
# 'cli' グループの下に 'validate' という名前のサブコマンドグループを作成.
@cli.group(help="Validate definition files.")
def validate():
    """定義ファイルを検証するコマンドグループ."""
    pass

# 3. 'data-dependencies' コマンドを 'validate' グループの下に定義
# @validate.command() で 'validate' グループに属するコマンドを作成.
# コマンド名はデフォルトで関数名 (validate_data_dependencies) になるが,
# 明示的に "data-dependencies" と指定.
@validate.command("data-dependencies")
# @click.argument() でコマンドライン引数を定義.
# 'filepath' という名前の必須引数を定義.
# type=click.Path(...) で引数の型を指定し、検証ルールを設定.
#   - exists=True: ファイル/ディレクトリが存在する必要がある.
#   - file_okay=True: ファイルを許可.
#   - dir_okay=False: ディレクトリを不許可.
#   - readable=True: 読み取り可能である必要がある.
#   - resolve_path=True: 相対パスを絶対パスに解決.
#   - path_type=Path: 受け取った値を pathlib.Path オブジェクトに変換.
@click.argument(
    "filepath",
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
        path_type=Path,
    ),
)
def validate_data_dependencies(filepath: Path):
    """
    data_dependencies.yml ファイルを検証する.
    """
    # click.echo() は print() と似ているが, click アプリケーションでの
    # 出力に適した関数.
    click.echo(f"Validating data dependencies file: {filepath}")
    validator = DataDependenciesValidator(filepath)
    is_valid = validator.validate() # validate() はエラーがあれば False を返す

    # バリデーションに失敗した場合 (エラーがあった場合)
    if not is_valid:
        # validator.validate() 内の _print_results でエラーメッセージは
        # 表示されているはず.
        # click.exceptions.Exit(code=1) を発生させ、
        # 終了コード 1 (エラーを示す) でプログラムを終了させる.
        raise click.exceptions.Exit(code=1)
    # is_valid が True の場合、関数は正常に終了し、
    # 暗黙的に終了コード 0 (成功) となる.

# スクリプトが直接実行された場合にメインの cli グループを実行
if __name__ == "__main__":
    cli()

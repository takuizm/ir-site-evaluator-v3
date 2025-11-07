"""ロガー設定

loguruを使用したロギング機能を提供する。
"""
from loguru import logger
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    level: str = "INFO",
    log_file: Optional[str] = None,
    console: bool = True,
    format_str: Optional[str] = None
):
    """ロガーを設定する

    Args:
        level: ログレベル (DEBUG, INFO, WARNING, ERROR)
        log_file: ログファイルパス（Noneの場合はファイル出力なし）
        console: コンソールへの出力を有効にするか
        format_str: ログフォーマット文字列

    Returns:
        設定されたロガーインスタンス
    """
    # デフォルトハンドラを削除
    logger.remove()

    # デフォルトフォーマット
    if format_str is None:
        format_str = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<level>{message}</level>"
        )

    # コンソール出力
    if console:
        logger.add(
            sys.stdout,
            level=level,
            format=format_str,
            colorize=True
        )

    # ファイル出力
    if log_file:
        # ログファイルのディレクトリを作成
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            log_file,
            level=level,
            format=(
                "{time:YYYY-MM-DD HH:mm:ss} | "
                "{level: <8} | "
                "{message}"
            ),
            rotation="10 MB",  # 10MBでローテーション
            retention="7 days",  # 7日間保持
            compression="zip",  # 圧縮
            encoding="utf-8"
        )

    return logger


def get_logger():
    """ロガーインスタンスを取得する

    Returns:
        ロガーインスタンス
    """
    return logger

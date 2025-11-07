"""設定管理

config.yamlと環境変数から設定を読み込み、管理する。
"""
import yaml
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Literal, List
from dotenv import load_dotenv


@dataclass
class APIConfig:
    """API設定"""
    provider: Literal['claude', 'openai']
    model: str
    api_key: str
    max_tokens: int
    max_retries: int
    timeout: int
    rate_limit_delay: float


@dataclass
class ScrapingConfig:
    """スクレイピング設定"""
    headless: bool
    wait_until: Literal['load', 'domcontentloaded', 'networkidle']
    delay_after_load: float
    timeout: int
    user_agent: str
    max_parallel: int
    screenshot_on_error: bool


@dataclass
class ProcessingConfig:
    """処理設定"""
    checkpoint_interval: int
    batch_semantic_checks: bool
    skip_errors: bool
    max_retries_per_site: int
    enable_parallel: bool = False  # サイトレベル並列実行の有効/無効
    max_parallel_sites: int = 5    # 同時に処理するサイト数
    enable_item_parallel: bool = False  # 項目レベル並列実行の有効/無効
    max_parallel_items_per_site: int = 10  # サイト内で同時に処理する項目数


@dataclass
class LoggingConfig:
    """ログ設定"""
    level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR']
    file: str
    console: bool
    format: str


@dataclass
class OutputConfig:
    """出力設定"""
    summary_csv: str
    detailed_csv: str
    error_log: str
    checkpoint_dir: str


@dataclass
class InputConfig:
    """入力設定"""
    sites_list: str
    validation_items: str


@dataclass
class PerformanceConfig:
    """パフォーマンス設定"""
    enable_caching: bool
    cache_dir: str
    max_cache_size_mb: int


@dataclass
class Config:
    """全体設定

    config.yamlと環境変数から読み込んだ設定を保持する。
    """
    api: APIConfig
    scraping: ScrapingConfig
    processing: ProcessingConfig
    logging: LoggingConfig
    output: OutputConfig
    input: InputConfig
    performance: PerformanceConfig

    @classmethod
    def load(cls, config_path: str = 'config.yaml', env_path: str = '.env') -> 'Config':
        """設定ファイルと環境変数から設定を読み込む

        Args:
            config_path: config.yamlのパス
            env_path: .envファイルのパス

        Returns:
            Configインスタンス

        Raises:
            FileNotFoundError: 設定ファイルが存在しない
            ValueError: 必須設定が不足している
        """
        # .envファイル読み込み
        if Path(env_path).exists():
            load_dotenv(env_path)

        # config.yaml読み込み
        if not Path(config_path).exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # API設定
        api_config = cls._load_api_config(data)

        # スクレイピング設定
        scraping_config = ScrapingConfig(
            headless=data['scraping']['headless'],
            wait_until=data['scraping']['wait_until'],
            delay_after_load=data['scraping']['delay_after_load'],
            timeout=data['scraping']['timeout'],
            user_agent=data['scraping']['user_agent'],
            max_parallel=data['scraping']['max_parallel'],
            screenshot_on_error=data['scraping']['screenshot_on_error']
        )

        # 処理設定
        processing_config = ProcessingConfig(
            checkpoint_interval=data['processing']['checkpoint_interval'],
            batch_semantic_checks=data['processing']['batch_semantic_checks'],
            skip_errors=data['processing']['skip_errors'],
            max_retries_per_site=data['processing']['max_retries_per_site'],
            enable_parallel=data['processing'].get('enable_parallel', False),
            max_parallel_sites=data['processing'].get('max_parallel_sites', 5),
            enable_item_parallel=data['processing'].get('enable_item_parallel', False),
            max_parallel_items_per_site=data['processing'].get('max_parallel_items_per_site', 10)
        )

        # ログ設定
        logging_config = LoggingConfig(
            level=data['logging']['level'],
            file=data['logging']['file'],
            console=data['logging']['console'],
            format=data['logging']['format']
        )

        # 出力設定
        output_config = OutputConfig(
            summary_csv=data['output']['summary_csv'],
            detailed_csv=data['output']['detailed_csv'],
            error_log=data['output']['error_log'],
            checkpoint_dir=data['output']['checkpoint_dir']
        )

        # 入力設定
        input_config = InputConfig(
            sites_list=data['input']['sites_list'],
            validation_items=data['input']['validation_items']
        )

        # パフォーマンス設定
        performance_config = PerformanceConfig(
            enable_caching=data['performance']['enable_caching'],
            cache_dir=data['performance']['cache_dir'],
            max_cache_size_mb=data['performance']['max_cache_size_mb']
        )

        return cls(
            api=api_config,
            scraping=scraping_config,
            processing=processing_config,
            logging=logging_config,
            output=output_config,
            input=input_config,
            performance=performance_config
        )

    @staticmethod
    def _load_api_config(data: dict) -> APIConfig:
        """API設定を読み込む

        Args:
            data: config.yamlのデータ

        Returns:
            APIConfigインスタンス

        Raises:
            ValueError: API Keyが見つからない
        """
        provider = data['api']['provider']

        if provider == 'claude':
            api_key_env = data['api']['claude']['api_key_env']
            model = data['api']['claude']['model']
            max_tokens = data['api']['claude']['max_tokens']
        elif provider == 'openai':
            api_key_env = data['api']['openai']['api_key_env']
            model = data['api']['openai']['model']
            max_tokens = data['api']['openai']['max_tokens']
        else:
            raise ValueError(f"Unknown API provider: {provider}")

        # 環境変数からAPI Key取得
        api_key = os.getenv(api_key_env)
        if not api_key:
            raise ValueError(
                f"API Key not found in environment variable: {api_key_env}. "
                f"Please set it in .env file or export it."
            )

        return APIConfig(
            provider=provider,
            model=model,
            api_key=api_key,
            max_tokens=max_tokens,
            max_retries=data['api']['max_retries'],
            timeout=data['api']['timeout'],
            rate_limit_delay=data['api']['rate_limit_delay']
        )

    def validate(self) -> List[str]:
        """設定のバリデーション

        Returns:
            エラーメッセージのリスト（空ならバリデーション成功）
        """
        errors = []

        # API設定の検証
        if self.api.max_retries < 0:
            errors.append("api.max_retries must be >= 0")
        if self.api.timeout <= 0:
            errors.append("api.timeout must be > 0")
        if self.api.rate_limit_delay < 0:
            errors.append("api.rate_limit_delay must be >= 0")

        # スクレイピング設定の検証
        if self.scraping.timeout <= 0:
            errors.append("scraping.timeout must be > 0")
        if self.scraping.max_parallel <= 0:
            errors.append("scraping.max_parallel must be > 0")

        # 処理設定の検証
        if self.processing.checkpoint_interval <= 0:
            errors.append("processing.checkpoint_interval must be > 0")

        # 入力ファイルの存在確認
        if not Path(self.input.sites_list).exists():
            errors.append(f"Input file not found: {self.input.sites_list}")
        if not Path(self.input.validation_items).exists():
            errors.append(f"Input file not found: {self.input.validation_items}")

        return errors

    def create_output_dirs(self):
        """出力ディレクトリを作成する"""
        # output/ ディレクトリ
        output_dir = Path(self.output.summary_csv).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # checkpoint/ ディレクトリ
        Path(self.output.checkpoint_dir).mkdir(parents=True, exist_ok=True)

        # cache/ ディレクトリ（有効な場合）
        if self.performance.enable_caching:
            Path(self.performance.cache_dir).mkdir(parents=True, exist_ok=True)

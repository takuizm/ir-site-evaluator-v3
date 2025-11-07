"""LLM API クライアント

Claude API と OpenAI API を統一インターフェースで扱う。
"""
import anthropic
import openai
import time
from typing import Optional


class LLMClient:
    """LLM API クライアント

    Claude と OpenAI の両方をサポート。
    レート制限対応、リトライロジック、コスト推定機能を提供。
    """

    def __init__(self, config, logger):
        """初期化

        Args:
            config: APIConfig インスタンス
            logger: ロガーインスタンス
        """
        self.config = config
        self.logger = logger
        self.provider = config.provider
        self.total_calls = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0

        # API クライアント初期化
        if self.provider == 'claude':
            self.client = anthropic.Anthropic(api_key=config.api_key)
            self.logger.info(f"Initialized Claude API client (model: {config.model})")
        elif self.provider == 'openai':
            self.client = openai.OpenAI(api_key=config.api_key)
            self.logger.info(f"Initialized OpenAI API client (model: {config.model})")
        else:
            raise ValueError(f"Unknown API provider: {self.provider}")

    def call(self, prompt: str, context: str) -> str:
        """LLM を呼び出す

        Args:
            prompt: システムプロンプト
            context: ユーザーコンテキスト

        Returns:
            LLMからの応答テキスト

        Raises:
            Exception: API呼び出しに失敗した場合
        """
        for attempt in range(self.config.max_retries):
            try:
                if self.provider == 'claude':
                    response_text = self._call_claude(prompt, context)
                else:
                    response_text = self._call_openai(prompt, context)

                self.total_calls += 1
                return response_text

            except anthropic.RateLimitError as e:
                self.logger.warning(f"Rate limit hit, waiting 60s... (attempt {attempt + 1}/{self.config.max_retries})")
                time.sleep(60)

            except openai.RateLimitError as e:
                self.logger.warning(f"Rate limit hit, waiting 60s... (attempt {attempt + 1}/{self.config.max_retries})")
                time.sleep(60)

            except (anthropic.APIError, openai.APIError) as e:
                self.logger.warning(f"API error: {e} (attempt {attempt + 1}/{self.config.max_retries})")
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.rate_limit_delay * (2 ** attempt))  # 指数バックオフ
                else:
                    raise

            except Exception as e:
                self.logger.error(f"Unexpected error during LLM call: {e}")
                raise

        raise Exception(f"Max retries ({self.config.max_retries}) exceeded for LLM call")

    def _call_claude(self, prompt: str, context: str) -> str:
        """Claude API を呼び出す

        Args:
            prompt: システムプロンプト
            context: ユーザーコンテキスト

        Returns:
            応答テキスト
        """
        self.logger.debug(f"Calling Claude API (model: {self.config.model})...")

        message = self.client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": f"{prompt}\n\n{context}"
                }
            ],
            timeout=self.config.timeout
        )

        # トークン数を記録
        self.total_input_tokens += message.usage.input_tokens
        self.total_output_tokens += message.usage.output_tokens

        self.logger.debug(
            f"Claude API call successful "
            f"(input: {message.usage.input_tokens}, output: {message.usage.output_tokens})"
        )

        return message.content[0].text

    def _call_openai(self, prompt: str, context: str) -> str:
        """OpenAI API を呼び出す

        Args:
            prompt: システムプロンプト
            context: ユーザーコンテキスト

        Returns:
            応答テキスト
        """
        self.logger.debug(f"Calling OpenAI API (model: {self.config.model})...")

        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": context}
            ],
            max_tokens=self.config.max_tokens,
            timeout=self.config.timeout
        )

        # トークン数を記録
        if response.usage:
            self.total_input_tokens += response.usage.prompt_tokens
            self.total_output_tokens += response.usage.completion_tokens

            self.logger.debug(
                f"OpenAI API call successful "
                f"(input: {response.usage.prompt_tokens}, output: {response.usage.completion_tokens})"
            )

        return response.choices[0].message.content

    def estimate_cost(self) -> dict:
        """現在までのコストを推定する

        Returns:
            コスト情報の辞書
        """
        if self.provider == 'claude':
            # Claude料金 (2024年10月時点)
            if 'sonnet' in self.config.model.lower():
                input_cost_per_m = 3.00  # $3.00 / 1M tokens
                output_cost_per_m = 15.00  # $15.00 / 1M tokens
            elif 'haiku' in self.config.model.lower():
                input_cost_per_m = 0.25  # $0.25 / 1M tokens
                output_cost_per_m = 1.25  # $1.25 / 1M tokens
            else:
                input_cost_per_m = 3.00
                output_cost_per_m = 15.00

        elif self.provider == 'openai':
            # OpenAI料金 (2024年10月時点)
            if 'gpt-4o-mini' in self.config.model.lower():
                input_cost_per_m = 0.150  # $0.150 / 1M tokens
                output_cost_per_m = 0.600  # $0.600 / 1M tokens
            elif 'gpt-4o' in self.config.model.lower():
                input_cost_per_m = 2.50  # $2.50 / 1M tokens
                output_cost_per_m = 10.00  # $10.00 / 1M tokens
            else:
                input_cost_per_m = 2.50
                output_cost_per_m = 10.00

        else:
            input_cost_per_m = 0.0
            output_cost_per_m = 0.0

        input_cost = (self.total_input_tokens / 1_000_000) * input_cost_per_m
        output_cost = (self.total_output_tokens / 1_000_000) * output_cost_per_m
        total_cost = input_cost + output_cost

        return {
            'provider': self.provider,
            'model': self.config.model,
            'total_calls': self.total_calls,
            'input_tokens': self.total_input_tokens,
            'output_tokens': self.total_output_tokens,
            'input_cost_usd': round(input_cost, 4),
            'output_cost_usd': round(output_cost, 4),
            'total_cost_usd': round(total_cost, 4)
        }

    def print_cost_summary(self):
        """コストサマリーをログ出力する"""
        cost_info = self.estimate_cost()
        self.logger.info("=" * 60)
        self.logger.info("LLM API Cost Summary")
        self.logger.info("=" * 60)
        self.logger.info(f"Provider: {cost_info['provider']}")
        self.logger.info(f"Model: {cost_info['model']}")
        self.logger.info(f"Total API Calls: {cost_info['total_calls']}")
        self.logger.info(f"Input Tokens: {cost_info['input_tokens']:,}")
        self.logger.info(f"Output Tokens: {cost_info['output_tokens']:,}")
        self.logger.info(f"Input Cost: ${cost_info['input_cost_usd']:.4f}")
        self.logger.info(f"Output Cost: ${cost_info['output_cost_usd']:.4f}")
        self.logger.info(f"Total Cost: ${cost_info['total_cost_usd']:.4f}")
        self.logger.info("=" * 60)

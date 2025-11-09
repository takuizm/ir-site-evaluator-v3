"""IRサイト評価ツール - メインスクリプト

全体のオーケストレーションを行う。
"""
import asyncio
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional

from src.config import Config
from src.models import Site, ValidationItem, ValidationResult
from src.utils.logger import setup_logger, get_logger
from src.utils.scraper import Scraper
from src.utils.llm_client import LLMClient
from src.utils.reporter import Reporter
from src.utils.site_mapper import SiteMapper
from src.utils.target_page_mapper import get_target_urls
from src.utils.structure_extractor import extract_structure
from src.validators.script_validator import ScriptValidator
from src.validators.llm_validator import LLMValidator
from src.utils.criteria_loader import load_criteria_metadata
from src.utils.not_supported import get_not_supported_reason


class IRSiteEvaluator:
    """IRサイト評価ツールのメインクラス"""

    def __init__(self, config_path: str = 'config.yaml'):
        """初期化

        Args:
            config_path: 設定ファイルパス
        """
        # 設定読み込み
        self.config = Config.load(config_path)

        # 設定バリデーション
        errors = self.config.validate()
        if errors:
            raise ValueError(f"Config validation failed: {errors}")

        # 出力ディレクトリ作成
        self.config.create_output_dirs()

        # ロガー初期化
        self.logger = setup_logger(
            level=self.config.logging.level,
            log_file=self.config.logging.file,
            console=self.config.logging.console
        )

        self.logger.info("=" * 60)
        self.logger.info("IRサイト評価ツール 起動")
        self.logger.info("=" * 60)

        # コンポーネント初期化
        self.scraper = None
        self.llm_client = None
        self.script_validator = None
        self.llm_validator = None
        self.reporter = None

        # データ
        self.sites: List[Site] = []
        self.validation_items: List[ValidationItem] = []
        self.results: List[ValidationResult] = []

    async def run(self):
        """メイン実行"""
        try:
            start_time = datetime.now()

            # 1. データ読み込み
            self.load_data()

            # 2. コンポーネント初期化
            await self.initialize_components()

            # 3. メインループ（並列 or 直列）
            if self.config.processing.enable_parallel:
                self.logger.info(f"Parallel execution enabled (max_parallel_sites={self.config.processing.max_parallel_sites})")
                await self.main_loop_parallel()
            else:
                self.logger.info("Sequential execution")
                await self.main_loop()

            # 4. 結果出力
            self.generate_reports()

            # 5. 統計情報表示
            elapsed_time = datetime.now() - start_time
            self.print_summary(elapsed_time)

        except Exception as e:
            self.logger.error(f"Fatal error: {e}")
            raise
        finally:
            await self.cleanup()

    def load_data(self):
        """入力データを読み込む"""
        self.logger.info("Loading input data...")

        # sites_list.csv読み込み
        sites_df = pd.read_csv(self.config.input.sites_list)
        self.sites = [
            Site(
                site_id=row['site_id'],
                company_name=row['company_name'],
                url=row['url'],
                industry=row.get('industry'),
                note=row.get('note')
            )
            for _, row in sites_df.iterrows()
        ]
        self.logger.info(f"Loaded {len(self.sites)} sites")

        # validation_items.csv読み込み
        items_df = pd.read_csv(self.config.input.validation_items)
        self.validation_items = [
            ValidationItem(
                item_id=int(row['item_id']),
                category=str(row['category']) if pd.notna(row['category']) else '',
                subcategory=str(row['subcategory']) if pd.notna(row['subcategory']) else '',
                item_name=str(row['item_name']) if pd.notna(row['item_name']) else '',
                automation_type=str(row['automation_type']) if pd.notna(row['automation_type']) else '',
                check_type=str(row['check_type']) if pd.notna(row['check_type']) else '',
                priority=str(row['priority']) if pd.notna(row['priority']) else '',
                difficulty=int(row['difficulty']),
                instruction=str(row['instruction']) if pd.notna(row['instruction']) else '',
                target_page=str(row['target_page']) if pd.notna(row['target_page']) else '',
                original_no=int(row['original_no']) if pd.notna(row['original_no']) else 0
            )
            for _, row in items_df.iterrows()
        ]
        self.logger.info(f"Loaded {len(self.validation_items)} validation items")

    async def initialize_components(self):
        """コンポーネントを初期化する"""
        self.logger.info("Initializing components...")

        # Scraper
        self.scraper = Scraper(self.config.scraping, self.logger)
        await self.scraper.initialize()

        # LLM Client
        self.llm_client = LLMClient(self.config.api, self.logger)

        # Validators
        self.script_validator = ScriptValidator(self.scraper, self.logger)
        self.llm_validator = LLMValidator(self.llm_client, self.logger)

        # Site Mapper
        self.site_mapper = SiteMapper()

        criteria_metadata, criteria_columns = load_criteria_metadata(Path('docs/criteria_org.csv'))
        item_lookup = {item.item_id: getattr(item, 'original_no', None) for item in self.validation_items}
        self.reporter = Reporter(
            self.config.output,
            self.logger,
            item_lookup=item_lookup,
            criteria_metadata=criteria_metadata,
            criteria_columns=criteria_columns
        )

        self.logger.info("All components initialized")

    async def _collect_page_assets(self, page_cache: dict) -> Tuple[dict, dict]:
        """HTMLおよび構造メタデータのキャッシュを生成"""
        html_cache = {}
        structure_cache = {}

        for url, page in page_cache.items():
            try:
                html = await page.content()
                html_cache[url] = html
                structure_cache[url] = extract_structure(html)
            except Exception as e:
                self.logger.warning(f"  Failed to capture HTML for {url}: {e}")
                html_cache[url] = ""
                structure_cache[url] = None

        return html_cache, structure_cache

    async def main_loop(self):
        """メインループ: 全サイト×全項目を検証（サブページ対応版）"""
        total_checks = len(self.sites) * len(self.validation_items)
        self.logger.info(f"Starting validation: {len(self.sites)} sites × {len(self.validation_items)} items = {total_checks} checks")

        for site_idx, site in enumerate(self.sites, 1):
            self.logger.info(f"[{site_idx}/{len(self.sites)}] Processing: {site.company_name} ({site.url})")

            try:
                # Step 1: IRトップページを開いてサイト構造をマッピング
                self.logger.info(f"  Mapping site structure...")
                ir_top_page = await self.scraper.get_page(site.url)
                site_map = await self.site_mapper.map_site(ir_top_page, site.url)

                # Step 2: 必要なページURLを特定
                required_urls = set([site.url])  # IRトップは必須
                for item in self.validation_items:
                    target_urls = get_target_urls(item, site_map)
                    required_urls.update(target_urls)

                self.logger.info(f"  Required pages: {len(required_urls)} URLs")

                # Step 3: 必要なページを取得してキャッシュ
                page_cache = {site.url: ir_top_page}  # IRトップは既に開いている

                for url in required_urls:
                    if url != site.url:  # IRトップ以外
                        try:
                            self.logger.debug(f"  Loading: {url}")
                            page_cache[url] = await self.scraper.get_page(url)
                        except Exception as e:
                            self.logger.warning(f"  Failed to load {url}: {e}")
                            # ページ取得失敗時はIRトップをフォールバック
                            page_cache[url] = ir_top_page

                # Step 3.5: HTML/構造キャッシュ
                html_cache, structure_cache = await self._collect_page_assets(page_cache)

                # Step 4: 各検証項目を適切なページで実行
                for item_idx, item in enumerate(self.validation_items, 1):
                    target_urls = get_target_urls(item, site_map)
                    payloads = self._build_page_payloads(
                        site,
                        item,
                        target_urls,
                        page_cache,
                        html_cache,
                        structure_cache,
                        site.url
                    )

                    result = await self._evaluate_item_with_payloads(site, item, payloads)
                    self.results.append(result)

                    log_msg = f"  [{item_idx}/{len(self.validation_items)}] {item.item_name}: {result.result}"
                    if result.result == 'PASS':
                        self.logger.info(log_msg)
                    elif result.result == 'FAIL':
                        self.logger.warning(log_msg)
                    else:
                        self.logger.error(log_msg)

                # Step 5: 全ページをクローズ
                for url, page in page_cache.items():
                    try:
                        await self.scraper.close_page(page)
                    except Exception as e:
                        self.logger.debug(f"  Failed to close page {url}: {e}")

                # チェックポイント保存
                if site_idx % self.config.processing.checkpoint_interval == 0:
                    self.save_checkpoint(site_idx)

            except Exception as e:
                self.logger.error(f"Failed to process site {site.company_name}: {e}")
                if not self.config.processing.skip_errors:
                    raise

    async def process_single_site(self, site: Site, site_idx: int, semaphore: asyncio.Semaphore, total_sites: int) -> List[ValidationResult]:
        """単一サイトを処理（並列実行対応）

        Args:
            site: 処理対象サイト
            site_idx: サイトのインデックス（1始まり）
            semaphore: 並列実行数を制限するSemaphore
            total_sites: 総サイト数

        Returns:
            このサイトの全検証結果のリスト
        """
        async with semaphore:  # 同時実行数を制限
            site_results = []
            self.logger.info(f"[{site_idx}/{total_sites}] Processing: {site.company_name} ({site.url})")

            try:
                # Step 1: IRトップページを開いてサイト構造をマッピング
                self.logger.info(f"  Mapping site structure...")
                ir_top_page = await self.scraper.get_page(site.url)
                site_map = await self.site_mapper.map_site(ir_top_page, site.url)

                # Step 2: 必要なページURLを特定
                required_urls = set([site.url])  # IRトップは必須
                for item in self.validation_items:
                    target_urls = get_target_urls(item, site_map)
                    required_urls.update(target_urls)

                self.logger.info(f"  Required pages: {len(required_urls)} URLs")

                # Step 3: 必要なページを取得してキャッシュ
                page_cache = {site.url: ir_top_page}  # IRトップは既に開いている

                for url in required_urls:
                    if url != site.url:  # IRトップ以外
                        try:
                            self.logger.debug(f"  Loading: {url}")
                            page_cache[url] = await self.scraper.get_page(url)
                        except Exception as e:
                            self.logger.warning(f"  Failed to load {url}: {e}")
                            # ページ取得失敗時はIRトップをフォールバック
                            page_cache[url] = ir_top_page

                # Step 3.5: HTML/構造キャッシュ
                html_cache, structure_cache = await self._collect_page_assets(page_cache)

                # Step 4: 各検証項目を適切なページで実行
                # 項目並列化が有効な場合は並列実行、無効な場合は直列実行
                if self.config.processing.enable_item_parallel:
                    site_results = await self._validate_items_parallel(
                        site,
                        page_cache,
                        html_cache,
                        structure_cache,
                        site_map,
                        ir_top_page
                    )
                else:
                    site_results = await self._validate_items_sequential(
                        site,
                        page_cache,
                        html_cache,
                        structure_cache,
                        site_map,
                        ir_top_page
                    )

                # Step 5: 全ページをクローズ
                for url, page in page_cache.items():
                    try:
                        await self.scraper.close_page(page)
                    except Exception as e:
                        self.logger.debug(f"  Failed to close page {url}: {e}")

            except Exception as e:
                self.logger.error(f"Failed to process site {site.company_name}: {e}")
                if not self.config.processing.skip_errors:
                    raise

            return site_results

    async def main_loop_parallel(self):
        """並列版メインループ: 全サイト×全項目を検証"""
        total_checks = len(self.sites) * len(self.validation_items)
        self.logger.info(f"Starting validation: {len(self.sites)} sites × {len(self.validation_items)} items = {total_checks} checks")

        # Semaphoreで同時実行数を制限
        max_parallel = self.config.processing.max_parallel_sites
        semaphore = asyncio.Semaphore(max_parallel)

        # 全サイトのタスクを作成
        tasks = [
            self.process_single_site(site, idx, semaphore, len(self.sites))
            for idx, site in enumerate(self.sites, 1)
        ]

        # 並列実行
        self.logger.info(f"Executing {len(tasks)} sites in parallel (max {max_parallel} concurrent)")
        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        # 結果を統合
        for idx, site_results in enumerate(results_list, 1):
            if isinstance(site_results, Exception):
                self.logger.error(f"Site {idx} failed with exception: {site_results}")
                # skip_errors=Trueの場合は続行
            else:
                self.results.extend(site_results)

                # チェックポイント保存
                if idx % self.config.processing.checkpoint_interval == 0:
                    self.save_checkpoint(idx)


    async def _validate_items_sequential(self, site: Site, page_cache: dict, html_cache: dict, structure_cache: dict, site_map: dict, ir_top_page) -> List[ValidationResult]:
        """項目を直列実行する（後方互換性のため）

        Args:
            site: サイト情報
            page_cache: ページオブジェクトキャッシュ
            html_cache: HTMLキャッシュ
            site_map: サイトマップ
            ir_top_page: IRトップページ

        Returns:
            検証結果のリスト
        """
        results = []
        for item_idx, item in enumerate(self.validation_items, 1):
            target_urls = get_target_urls(item, site_map)
            payloads = self._build_page_payloads(
                site,
                item,
                target_urls,
                page_cache,
                html_cache,
                structure_cache,
                site.url
            )

            result = await self._evaluate_item_with_payloads(site, item, payloads)
            results.append(result)

            log_msg = f"  [{item_idx}/{len(self.validation_items)}] {item.item_name}: {result.result}"
            if result.result == 'PASS':
                self.logger.info(log_msg)
            elif result.result == 'FAIL':
                self.logger.warning(log_msg)
            else:
                self.logger.error(log_msg)

        return results

    async def _validate_items_parallel(self, site: Site, page_cache: dict, html_cache: dict, structure_cache: dict, site_map: dict, ir_top_page) -> List[ValidationResult]:
        """項目をバッチ並列実行する（LLM検証のみ）

        Args:
            site: サイト情報
            page_cache: ページオブジェクトキャッシュ
            html_cache: HTMLキャッシュ
            site_map: サイトマップ
            ir_top_page: IRトップページ

        Returns:
            検証結果のリスト
        """
        # Script検証とLLM検証を分離
        script_items = [item for item in self.validation_items if item.check_type == 'script']
        llm_items = [item for item in self.validation_items if item.check_type == 'llm']

        self.logger.info(f"  Item parallelization: {len(script_items)} script (sequential) + {len(llm_items)} LLM (parallel)")

        all_results = []

        # Script検証: 直列実行（高速なのでそのまま）
        for item_idx, item in enumerate(script_items, 1):
            payloads = self._build_page_payloads(
                site,
                item,
                get_target_urls(item, site_map),
                page_cache,
                html_cache,
                structure_cache,
                site.url
            )

            result = await self._run_script_validations(site, item, payloads)
            all_results.append(result)

            log_msg = f"  [Script {item_idx}/{len(script_items)}] {item.item_name}: {result.result}"
            if result.result == 'PASS':
                self.logger.info(log_msg)
            elif result.result == 'FAIL':
                self.logger.warning(log_msg)
            else:
                self.logger.error(log_msg)

        # LLM検証: バッチ並列実行
        max_batch_size = self.config.processing.max_parallel_items_per_site

        for batch_start in range(0, len(llm_items), max_batch_size):
            batch = llm_items[batch_start:batch_start + max_batch_size]
            self.logger.info(f"  Processing LLM batch {batch_start // max_batch_size + 1}/{(len(llm_items) + max_batch_size - 1) // max_batch_size}: {len(batch)} items")

            # バッチ内の全項目を並列実行
            tasks = []
            for item in batch:
                payloads = self._build_page_payloads(
                    site,
                    item,
                    get_target_urls(item, site_map),
                    page_cache,
                    html_cache,
                    structure_cache,
                    site.url
                )

                task = self.llm_validator.validate_with_pages(site, item, payloads)
                tasks.append(task)

            # 並列実行
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # 結果を収集
            for batch_item, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    self.logger.error(f"  LLM validation failed for {batch_item.item_name}: {result}")
                    result = ValidationResult(
                        site_id=site.site_id,
                        company_name=site.company_name,
                        url=site.url,
                        item_id=batch_item.item_id,
                        item_name=batch_item.item_name,
                        category=batch_item.category,
                        subcategory=batch_item.subcategory,
                        result='ERROR',
                        confidence=0.0,
                        details=str(result),
                        checked_at=datetime.now(),
                        checked_url=site.url,
                        error_message=str(result)
                    )

                all_results.append(result)

                # ログ出力
                log_msg = f"  [{len(all_results)}/{len(self.validation_items)}] {batch_item.item_name}: {result.result}"
                if result.result == 'PASS':
                    self.logger.info(log_msg)
                elif result.result == 'FAIL':
                    self.logger.warning(log_msg)
                else:
                    self.logger.error(log_msg)

        return all_results

    def _build_page_payloads(self, site: Site, item: ValidationItem, target_urls: List[str], page_cache: dict, html_cache: dict, structure_cache: dict, fallback_url: str) -> List[dict]:
        fallback_page = page_cache.get(fallback_url)
        fallback_html = html_cache.get(fallback_url, "")
        fallback_structure = structure_cache.get(fallback_url)

        payloads = []
        seen = set()
        for url in target_urls:
            resolved = url or fallback_url
            if resolved in seen:
                continue
            seen.add(resolved)
            payloads.append({
                'url': resolved,
                'page': page_cache.get(resolved, fallback_page),
                'html': html_cache.get(resolved, fallback_html),
                'structure': structure_cache.get(resolved, fallback_structure)
            })

        if not payloads:
            payloads.append({
                'url': fallback_url,
                'page': fallback_page,
                'html': fallback_html,
                'structure': fallback_structure
            })

        return payloads

    async def _run_script_validations(self, site: Site, item: ValidationItem, payloads: List[dict]) -> ValidationResult:
        last_result = None
        for idx, payload in enumerate(payloads):
            page = payload.get('page')
            if not page:
                continue
            result = await self.script_validator.validate(site, page, item, payload['url'])
            if result.result == 'PASS':
                if idx > 0:
                    result.details = f"別URL({payload['url']})でPASS: {result.details}"
                return result
            last_result = result

        if last_result:
            return last_result

        # ここまで来るのはページ取得に失敗した場合のみ
        return ValidationResult(
            site_id=site.site_id,
            company_name=site.company_name,
            url=site.url,
            item_id=item.item_id,
            item_name=item.item_name,
            category=item.category,
            subcategory=item.subcategory,
            result='ERROR',
            confidence=0.0,
            details='ページを取得できませんでした',
            checked_at=datetime.now(),
            checked_url=payloads[0]['url'] if payloads else site.url,
            error_message='page unavailable'
        )

    def _create_not_supported_result(self, site: Site, item: ValidationItem, checked_url: str, reason: str) -> ValidationResult:
        return ValidationResult(
            site_id=site.site_id,
            company_name=site.company_name,
            url=site.url,
            item_id=item.item_id,
            item_name=item.item_name,
            category=item.category,
            subcategory=item.subcategory,
            result='NOT_SUPPORTED',
            confidence=0.0,
            details=reason,
            checked_at=datetime.now(),
            checked_url=checked_url,
            error_message=None
        )

    async def _evaluate_item_with_payloads(self, site: Site, item: ValidationItem, payloads: List[dict]) -> ValidationResult:
        reason = get_not_supported_reason(item)
        if reason:
            checked_url = payloads[0]['url'] if payloads else site.url
            return self._create_not_supported_result(site, item, checked_url, reason)

        try:
            if item.check_type == 'script':
                return await self._run_script_validations(site, item, payloads)
            elif item.check_type == 'llm':
                return await self.llm_validator.validate_with_pages(site, item, payloads)
            else:
                raise ValueError(f"Unknown check_type: {item.check_type}")
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            return ValidationResult(
                site_id=site.site_id,
                company_name=site.company_name,
                url=site.url,
                item_id=item.item_id,
                item_name=item.item_name,
                category=item.category,
                subcategory=item.subcategory,
                result='ERROR',
                confidence=0.0,
                details=str(e),
                checked_at=datetime.now(),
                checked_url=payloads[0]['url'] if payloads else site.url,
                error_message=str(e)
            )

    def save_checkpoint(self, site_count: int):
        """チェックポイントを保存"""
        checkpoint_path = Path(self.config.output.checkpoint_dir) / f"checkpoint_{site_count}.csv"
        df = pd.DataFrame([r.to_dict() for r in self.results])
        df.to_csv(checkpoint_path, index=False, encoding='utf-8-sig')
        self.logger.info(f"Checkpoint saved: {checkpoint_path}")

    def generate_reports(self):
        """レポートを生成"""
        self.logger.info("Generating reports...")
        self.reporter.generate_summary_csv(self.results)
        self.reporter.generate_detailed_csv(self.results)
        self.logger.info("Reports generated successfully")

    def print_summary(self, elapsed_time):
        """サマリーを表示"""
        self.reporter.print_statistics(self.results)
        self.llm_client.print_cost_summary()
        self.logger.info(f"Total execution time: {elapsed_time}")

    async def cleanup(self):
        """クリーンアップ"""
        if self.scraper:
            await self.scraper.close()


async def main():
    """エントリーポイント"""
    import argparse
    parser = argparse.ArgumentParser(description='IRサイト評価ツール')
    parser.add_argument('--config', type=str, default='config.yaml', help='設定ファイルパス')
    args = parser.parse_args()

    evaluator = IRSiteEvaluator(config_path=args.config)
    await evaluator.run()


if __name__ == '__main__':
    asyncio.run(main())

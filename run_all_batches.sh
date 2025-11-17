#!/bin/bash
# 全バッチを順次実行するスクリプト

set -e  # エラー時に即座に終了

# 色付き出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# バッチ数を自動検出（input/batch_*.csvファイルの数）
BATCH_COUNT=$(ls input/batch_*.csv 2>/dev/null | wc -l | tr -d ' ')

if [ "$BATCH_COUNT" -eq 0 ]; then
    echo -e "${RED}❌ Error: No batch files found in input/batch_*.csv${NC}"
    echo -e "${YELLOW}💡 Please run: python split_sites.py${NC}"
    exit 1
fi

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}🚀 Starting Batch Execution${NC}"
echo -e "${BLUE}=========================================${NC}"
echo -e "Total batches: ${BATCH_COUNT}"
echo -e "Start time: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 開始時刻を記録
START_TIME=$(date +%s)

# バッチごとに実行
for i in $(seq 1 $BATCH_COUNT); do
    BATCH_NUM=$(printf "%02d" $i)
    BATCH_FILE="input/batch_${BATCH_NUM}.csv"
    OUTPUT_FILE="output/batch_${BATCH_NUM}_results.csv"
    DETAILED_FILE="output/batch_${BATCH_NUM}_detailed.csv"
    CHECKPOINT_DIR="checkpoint/batch_${BATCH_NUM}"
    LOG_FILE="output/batch_${BATCH_NUM}_execution.log"

    echo -e "${YELLOW}=========================================${NC}"
    echo -e "${YELLOW}📦 Batch ${i}/${BATCH_COUNT}: ${BATCH_FILE}${NC}"
    echo -e "${YELLOW}=========================================${NC}"

    # サイト数を表示
    SITE_COUNT=$(awk 'END {print NR-1}' "$BATCH_FILE")
    echo -e "Sites in this batch: ${SITE_COUNT}"
    echo -e "Start time: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    # バッチ実行用の一時設定ファイルを作成
    TEMP_CONFIG="config_batch_${BATCH_NUM}.yaml"

    # ベース設定ファイルをコピーして、バッチ固有の値を上書き
    cat > "$TEMP_CONFIG" <<EOF
# バッチ ${BATCH_NUM} 用の一時設定ファイル（自動生成）

# API設定
api:
  provider: "openai"
  claude:
    model: "claude-3-5-sonnet-20241022"
    api_key_env: "ANTHROPIC_API_KEY"
    max_tokens: 4096
  openai:
    model: "gpt-4o-mini"
    api_key_env: "OPENAI_API_KEY"
    max_tokens: 4096
  max_retries: 3
  timeout: 60
  rate_limit_delay: 0.5

# スクレイピング設定
scraping:
  headless: true
  wait_until: "domcontentloaded"
  delay_after_load: 5.0
  timeout: 60
  user_agent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
  max_parallel: 1
  screenshot_on_error: true

# 処理設定
processing:
  checkpoint_interval: 1
  batch_semantic_checks: true
  skip_errors: true
  max_retries_per_site: 2
  enable_parallel: false
  max_parallel_sites: 1
  enable_item_parallel: false
  max_parallel_items_per_site: 10

# ログ設定
logging:
  level: "INFO"
  file: "${LOG_FILE}"
  console: true
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 出力設定
output:
  summary_csv: "${OUTPUT_FILE}"
  detailed_csv: "${DETAILED_FILE}"
  error_log: "output/batch_${BATCH_NUM}_error_log.txt"
  checkpoint_dir: "${CHECKPOINT_DIR}"

# 入力設定
input:
  sites_list: "${BATCH_FILE}"
  validation_items: "input/validation_items.csv"

# パフォーマンス設定
performance:
  enable_caching: true
  cache_dir: ".cache"
  max_cache_size_mb: 500
EOF

    # バッチ実行
    BATCH_START=$(date +%s)

    python -m src.main --config "$TEMP_CONFIG" || {
        echo -e "${RED}❌ Batch ${i} failed${NC}"
        echo -e "${YELLOW}💡 You can retry with the same command:${NC}"
        echo -e "   python -m src.main --config $TEMP_CONFIG"
        exit 1
    }

    # 一時設定ファイルを削除
    rm -f "$TEMP_CONFIG"

    BATCH_END=$(date +%s)
    BATCH_DURATION=$((BATCH_END - BATCH_START))

    echo ""
    echo -e "${GREEN}✅ Batch ${i} completed successfully${NC}"
    echo -e "Duration: $((BATCH_DURATION / 60)) minutes $((BATCH_DURATION % 60)) seconds"
    echo -e "Output: ${OUTPUT_FILE}"
    echo ""
done

# 終了時刻を記録
END_TIME=$(date +%s)
TOTAL_DURATION=$((END_TIME - START_TIME))

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}🎉 All Batches Completed!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo -e "Total batches: ${BATCH_COUNT}"
echo -e "Total duration: $((TOTAL_DURATION / 3600)) hours $((TOTAL_DURATION % 3600 / 60)) minutes"
echo -e "End time: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo -e "${YELLOW}📊 Next step:${NC}"
echo -e "   Merge all results: ${BLUE}python merge_results.py${NC}"
echo ""

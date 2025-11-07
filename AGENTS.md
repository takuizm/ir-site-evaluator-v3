# Repository Guidelines

## Project Structure & Module Organization
Runtime logic lives in `src/`: `main.py` orchestrates async scraping, LLM calls, and reporting; `models.py` holds dataclasses; `validators/` implements script vs LLM checks; `utils/` stores scraper, logger, mapper, and reporter helpers. Canonical inputs stay in `input/`, generated artifacts in `output/`, and recovery data in `checkpoint/`. Keep documentation in `docs/` and place any new automated checks alongside `tests/test_basic.py`.

## Build, Test, and Development Commands
- `pip install -r requirements.txt` — install runtime dependencies inside an activated virtualenv.
- `playwright install chromium` — provision the headless browser expected by `src/utils/scraper.py`.
- `python -m src.main --config config.yaml` — run a full IR-site evaluation; point `--config` to custom YAML for experiments.
- `python tests/test_basic.py` — bundled smoke covering imports, config validation, and CSV schemas.
- `pytest -q` — preferred once additional tests exist (install `pytest`; it is not pinned).

## Coding Style & Naming Conventions
Use Python 3.10+, 4-space indentation, and PEP 8 identifiers (snake_case functions, PascalCase classes). Follow the type-hinted dataclass pattern from `src/models.py`, validate inputs inside `__post_init__`, and keep enums explicit with `Literal`. New helpers should live in `src/utils/` with descriptive filenames, and shared constants belong near their consumers instead of a global mega-module. Emit operational detail via `loguru` (see `src/utils/logger.py`) rather than ad-hoc prints.

## Testing Guidelines
`tests/test_basic.py` ensures modules import, configs validate, and CSV schemas stay intact. Extend that module or add neighbors that exercise new validators, reporters, or scrapers, and keep tests runnable via both `pytest` and direct execution. When logic depends on CSV fixtures, add minimal samples under `tests/fixtures/` and assert both PASS and FAIL paths so regressions surface quickly.

## Commit & Pull Request Guidelines
History shows concise imperative summaries (`Initial commit: IR site evaluator v3`); mirror that style, keep subjects ≤72 characters, and add a colon only when a short qualifier helps. PRs should explain the problem solved, call out touched criteria IDs or config keys, list test evidence (commands or snippets from `output/results_summary.csv`), and note any new environment variables or secrets. Attach screenshots only when scraper-visible changes need proof.

## Security & Configuration Tips
Never commit `.env` or real customer CSVs—use `.env.example` plus sanitized samples in `input/`. When deviating from the default `config.yaml`, copy it (e.g., `config.staging.yaml`) and reference overrides in documentation. Clean `output/`, `checkpoint/`, and `execution.log` before pushing unless the diff intentionally demonstrates a new artifact format.

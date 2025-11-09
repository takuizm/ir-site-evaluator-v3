# VISUAL 観点 自動化ガイド

VISUAL カテゴリ（39件）を ScriptValidator から自動判定できるようにするための設計メモ。`src/utils/visual_checks.py` で Playwright ページから CSS 情報・スクリーンショット・要素寸法を取得し、ScriptValidator が PASS/FAIL を返すまでの流れを定義する。

## 1. `visual_checks` の構成

```text
src/utils/visual_checks.py
    ├─ VisualCheckResult (dataclass)  # selector, metrics, screenshot_path
    ├─ capture_visual_metrics(page, selectors) -> Dict[str, Any]
    ├─ evaluate_carousel(panel) -> dict {slide_count, has_pause_button, autoplay}
    ├─ evaluate_fv_size(panel) -> dict {height_ratio}
    ├─ compute_contrast(foreground, background) -> float
    ├─ analyze_calculated_styles(styles) -> dict  # しきい値チェック
    └─ take_element_screenshot(locator, label) -> path
```

`structure_extractor.capture_visual_context` が返す JSON をそのまま ScriptValidator へ渡すこともできるが、プレゼンテーション層に依存する観点が増えるため、VISUAL 用に薄いオーケストレータを用意して再利用性を上げる。

## 2. ScriptValidator からの呼び出し
- VISUAL 観点の `item_id` 一覧を `visual_checks_map` として保持し、ScriptValidator で Playwright `page` を渡して判定を実行。
- 例: `result = await self.visual_evaluator.check_carousel_size(page, item)` のような API を用意する。
- `ValidationResult.details` には `カルーセル3枚 / 停止ボタンあり / 高さ 620px` など、数値根拠を含める。

## 3. 判定しきい値（例）
|観点|条件|出力例|
|---|---|---|
|IRトップのカルーセル枚数 ≤3|`slide_count <= 3`|`カルーセル3枚（PASS）`|
|カルーセル停止ボタン|`has_pause_button is True`|`カルーセル停止ボタンあり`|
|FV 画像が大きすぎない|`hero_height / viewport_height <= 0.5`|`ファーストビュー高さ 42%`|
|コントラスト|`contrastRatio >= 4.5`|`コントラスト 5.2:1`|
|顔写真掲載|該当要素のスクリーンショット保存で検出|`代表写真を検出 (output/visual/hero.png)`|

## 4. VISUAL 観点別 PASS/FAIL 条件

|Criteria ID|item_id|観点|PASS 条件|FAIL 条件|備考|
|---|---|---|---|---|---|
|180|19|IRトップのカルーセルは3枚以下／動画10秒以下|カルーセルが3枚以下、またはカルーセル自体なし|4枚以上のスライドを検出、もしくは動画の長さが 10 秒超（※動画長自動計測は今後の課題）|`VisualAnalyzer.evaluate_carousels` の `slide_count` を参照|
|190|20|カルーセルに停止ボタンがある|自動再生設定のカルーセルに `hasPauseControl` が付与されている|自動再生なのに停止ボタンがない|`data-autoplay` や `swiper/slick` の既定属性を参照|
|195|21|ファーストビューが画面の 50% 以下|`hero_rect.height / viewport.height <= 0.5`|上記比率が 0.5 を超える|対象セレクタ: `.hero`, `.main-visual`, `.fv` など|
|200|22|ファーストビュー内にイベント予定|FV エリア内テキストに `決算/イベント/カンファレンス` と `日付` パターン両方存在|イベント文言または日付の片方のみ、あるいは両方無し|`capture_visual_context(..., selectors=HERO_SELECTORS)` + 正規表現|
|220|23|IRトップに IRニュース一覧|ニュースリスト要素（`section.news` 等）と複数記事エントリが見つかる|要素検出できず、もしくは1件以下|`locator('.news-list li')` の件数|
|240|25|IRトップにトップ(CEO)の顔写真|`.top-message img` など顔写真エリアのスクリーンショット取得に成功|該当画像を検出できず|Playwright locator + `VisualAnalyzer` でスクショ保存|
|244|29|代替テキスト（Alt）|`document.images` の 95%以上で `alt` が非空|`alt` 無し画像が5%以上|Playwright の `page.evaluate()` でカウント|
|245|30|色の違いに依存しないリンク表示|リンクの60%以上で下線または境界線等の装飾がある|装飾のあるリンクが60%未満|Playwrightで `text-decoration-line` / `border-bottom` を評価|
|246|31|カルーセル停止（WCAG2.0 A）|criteria 190 と同様に pause ボタンあり|自動再生なのに停止ボタンがない|item20 と共通ロジック|
|280|33|コントラスト比 4.5:1|`contrastRatio >= 4.5` の要素を検出|比率が 4.5 未満|`capture_visual_context` の styles から評価|
|270|37|基本文章の行間 150%以上|`line-height / font-size >= 1.5`|比率が 1.5 未満|CSS値を px で比較（normal=1.2 換算）|
|290|38|訪問済みリンクが色彩変化|CSS に `:visited` ルールが存在|`:visited` 定義が無い|`document.styleSheets` を走査|
|320|40|別ウィンドウリンク識別|`target="_blank"` のリンクの50%以上でアイコン/文言あり|指標未満|`check_external_link_icon` を流用|
|670|43|PDFリンク識別|PDFリンクの80%以上で「PDF」表記またはアイコン|指標未満|Playwright で `a[href*=".pdf"]` を解析|

> ※ 全 39 件の VISUAL 観点を順次この表に追記し、ScriptValidator 実装完了後に `result_type_map.csv` と同期する。

## 5. スクリーンショット保存ポリシー
- デフォルト保存先: `output/visual/<item_id>/<selector>.png`
- ScriptValidator の結果 CSV の `screenshot_path` にも同パスを格納しておくとレポートから辿れる。
- スクリーンショットは 800px 幅程度に縮小して保存（Pillow 等で最適化）することでストレージ節約。

## 6. 今後のロードマップ
1. `visual_checks.py` を実装し、カルーセル・FVサイズ・顔写真検出など優先5観点をスクリプト化。
2. `ScriptValidator` に VISUAL 観点のマッピングを追加し、LLM 観点から順次移行。
3. `docs/validation_capability.md` の VISUAL セクションに進捗を反映し、LLM/DOM の切り分け状況を定期アナウンス。

このドキュメントは VISUAL 判定ロジックの設計メモとして随時更新する。

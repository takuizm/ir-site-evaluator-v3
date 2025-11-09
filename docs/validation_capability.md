# Validation Capability Matrix

このドキュメントは 249 項目の評価観点を、「現在のツールでどう判定できるか」という観点で棚卸しした結果と、今後の改善計画をまとめたものです。判定種別は `analysis/result_type_map.csv` にエクスポートされています。

## 判定カテゴリの概要

|カテゴリ|件数|概要|次のアクション|
|---|---|---|---|
|DOM Script (`DOM`)|143|メニュー導線、パンくず、FAQ、PDFリンクなど DOM 情報があれば判断できる観点|`ScriptValidator` で観点と一致した details を自動生成（現状ほぼ全てスクリプト化済み）|
|Visual (`VISUAL`)|39|色/コントラスト、カルーセル、グラフ表示など視覚・レイアウトが根拠になる観点|CSS 値取得や要素スクリーンショット＋画像解析を設計し、LLM 依存を減らす|
|LLM Text (`LLM`)|106|文章内容・記載有無などテキスト中心の観点|構造 JSON と観点別テンプレートを使い、details が観点から逸脱しないよう制御|
|Not Supported (`NOT_SUPPORTED`)|13|サイト内検索チューニングなど複雑な操作/計測が必要な観点|`NOT_SUPPORTED` を返し理由を明示。Web Vitals 等の外部計測導入までは対象外|

> 数値は `analysis/result_type_map.csv`（2025-11-09更新）から集計。criteria_2025.md の「調査方法」とズレが見つかった場合は同ファイルを修正してください。

## `NOT_SUPPORTED` ポリシー
- `ValidationResult.result` に `NOT_SUPPORTED` を追加し、該当観点は無理に PASS/FAIL を出さず理由を明示します。
- 初期対象: Action Duration、LCP、CLS、TTFB、Speed Index、稼働率（item_id 53–59 ほか）。
- 将来的に Web Vitals やログ連携を実装したときにのみ PASS/FAIL に戻します。

## Web Vitals / 外部計測の方針（2025-11-08 更新）
- **対象指標**: Action Duration、LCP、CLS、TTFB、Speed Index、稼働率、TLS バージョン、PDF プロテクト有無、正常URL率など DOM だけでは測定できない 13 項目。
- **計測オプション比較**  
  |手段|長所|短所|現状|
  |---|---|---|---|
  |Playwright Tracing + `performance.getEntries()`|既存ブラウザを流用、LCP/TTFBを取得可能|CLS/Speed Index/稼働率は取得不可。大量保存でストレージ負荷|プロトタイプ調査中（未実装）|
  |Lighthouse CLI / PSI API|Web Vitals網羅、ベンチマーク済み|実行時間が長く、シングルスレッド処理・APIキーコストが大きい|導入検討中。個別実行用スクリプト設計予定|
  |外部監視サービス連携（SpeedCurve等）|稼働率/可用性ログを活用できる|有償サービス・API連携が必要|要件定義フェーズ|
  |サーバログ解析|正常URL率や404率を算出可|顧客インフラへのアクセスが必要|セキュリティ制約により当面見送り|
- **当面の結論**: 上記理由から本体ワークフローでは PASS/FAIL を出さず `NOT_SUPPORTED` を返す。将来は「Playwright計測→CSV保存→別ジョブでLighthouse補完」という二段構成を採用する。
- **追跡方法**: `src/utils/not_supported.py` に観点IDと理由を集約し、docs/TODO.md で Web Vitals 導入タスクを管理する。

## DOM/構造観点の強化ロードマップ
1. **要素抽出ライブラリ拡張**: `structure_extractor` でパンくず、FAQ、PDF/動画、ヘッダー固定など観点別 JSON を生成。
2. **ScriptValidator 移行**: 存在チェックで完結する項目を LLM から切り離し、観点に即した details を自動生成。
3. **LLM プロンプト最適化**: JSON を添付し、「JSON に含まれない情報を根拠にしない」指示と観点別テンプレートを整備。

## Visual 観点の対応方針
- **短期**: CSS プロパティ（`getComputedStyle`）や要素属性から推定できるものは ScriptValidator で検証。例: フォントサイズ、行間。
- **中期**: Playwright の `locator.screenshot()` で要素スクリーンショットを取得し、Pillow 等でコントラスト計算。カルーセル/ファーストビューは要素数と自動再生属性を DOM から取得。
- **長期**: 必要に応じてマルチモーダル LLM を活用。ただしコストと安定性を確認してから導入。

## 今後のステップ
1. `analysis/result_type_map.csv`（item_id / original_no / result_type / reason）を criteria_2025.md と突き合わせて都度更新。
2. `NOT_SUPPORTED` の観点はコードで明示し、details に測定不可の理由を出力（実装済み）。
3. DOM 観点（149件）のうち、details の改善が必要な項目を中心にロジックと説明文を強化。
4. Visual 観点（39件）向けに CSS 取得／スクリーンショット解析の仕組みを設計し、順次自動化。
5. LLM 観点（48件）は構造 JSON + 観点別テンプレートでプロンプトを最適化し、観点外の根拠を抑制。

このドキュメントは観点ごとの対応状況を定期的に更新し、開発タスクの優先順位付けに利用します。

## VISUAL 観点の進捗（2025-11-08 更新）
- Playwright + VisualAnalyzer で以下の VISUAL 項目 (item 19/20/21/22/23/25) を ScriptValidator に移行済み。
- `structure_extractor` で CSS/スクリーンショット/カルーセル情報を JSON へ出力し、LLM 経由の観点から視覚系を切り離す準備が完了。
- 残り VISUAL 項目は `docs/visual_checks.md` のテンプレを参照しつつ順次自動化予定。完了状況は `result_type_map.csv` と同期させて管理する。

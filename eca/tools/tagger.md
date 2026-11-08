# tagger — 画像タグ付けスクリプト

`SmilingWolf/wd-eva02-large-tagger-v3` を使ってアニメ画像を danbooru タグ(rating / character / general)でタグ付けする CLI スクリプト。**LLM から custom tool 経由で利用することを想定**しており、stdout は機械可読な JSON のみ、診断・エラーは stderr に分離されています。

## ファイル構成

| ファイル | 用途 |
|---|---|
| `tagger.py` | スクリプト本体(納品物) |
| `tagger.md` | このドキュメント(仕様) |
| `models/` | モデル重みと tag 一覧 CSV の配置先(ユーザーが手動 DL) |
| `tests/test_tagger.py` | 仕様に基づくテスト |
| `tests/data/` | E2E テスト用の正解タグ入り画像(tmp/ からコピーした恒久テストデータ) |

## 依存関係(グローバル Python で管理)

- **必須 (safetensors 経路 — 第一形式)**: `torch` (CPU build), `timm`, `safetensors`, `Pillow`, `numpy`
- **必須 (ONNX 経路 — 旧モデル用)**: `onnxruntime>=1.17.0` (上記と共通部分を除く)
- 現状グローバル Python 3.11 (`D:\Python311`) にすべて存在: torch 2.14.0+cpu, timm 1.0.29, safetensors 0.8.0, torchvision 0.29.0, onnxruntime 1.26.0, Pillow 10.1.0, numpy 2.4.6

torch を CPU 版で導入する場合 (Windows ではデフォルトの PyPI wheel が CUDA 同梱で巨大になる):

```
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install timm safetensors
```

## モデルファイルの手動 DL

配置先: `tagger/models/`

| ファイル | URL | 備考 |
|---|---|---|
| `model.safetensors` | https://huggingface.co/SmilingWolf/wd-eva02-large-tagger-v3/resolve/main/model.safetensors | **第一形式 (推奨)**。16473 クラス。**将来のモデル更新は safetensors 配布のみ** |
| `selected_tags.csv` | https://huggingface.co/SmilingWolf/wd-eva02-large-tagger-v3/resolve/main/selected_tags.csv | **必須** (新モデル用)。tag 一覧 (16473 行)。形式: `tag_id,name,category,count` |
| `model.onnx` | 同リポジトリの同名ファイル | 旧形式 (10861 クラス)。ONNX 経路で動作 |
| `selected_tags.csv.bak` | `selected_tags.csv` 更新時のバックアップ | 旧 CSV (10861 行)。`model.onnx` とのペアリングに必要 |
| `model.msgpack` | 同リポジトリの同名ファイル | 旧形式 (torch/timm 必要) |

⚠️ **モデルと CSV は行数 (クラス数) が一致するペアとして使うこと**。CSV の行順がモデルのクラスインデックスに対応するため、新旧を混用すると (行数違いの) サイズ不一致エラーになる。E2E テストもこのペアリングを前提にしている。

## CLI 契約

```
python tagger.py <image> [image ...] [--model PATH] [--tags PATH] [--threshold 0.35] [--limit 20] [--device cpu|gpu]
```

| 引数 | 既定 | 説明 |
|---|---|---|
| `images` | (必須) | 画像ファイル / ディレクトリ / glob。`jpg jpeg png bmp webp tga` を収集し、複数画像はバッチ推論 |
| `--model` | 環境変数 `TAGGER_MODEL` → `models/model.safetensors` → `models/model.onnx` → `models/model.msgpack` → `models/` 内を拡張子順に探索 | モデルファイルのパス。既定は safetensors 優先 (新モデル更新が safetensors 配布のみであるため) |
| `--tags` | 環境変数 `TAGGER_TAGS` → モデルと同じディレクトリの `selected_tags.csv` → `models/selected_tags.csv` | tag 一覧 CSV のパス |
| `--threshold` | `0.35` | スコア下限 |
| `--limit` | `20` | 画像ごとのタグ数上限(`0` で無制限) |
| `--device` | `cpu` | `gpu` は CUDA 対応 onnxruntime が必要。GPU 初期化失敗時は stderr に警告し CPU にフォールバック |

### 出力 (stdout — 成功時・JSON のみ)

```json
{
  "images": [
    {
      "file": "C:/path/to/img.jpg",
      "tags": [
        {"tag": "1girl", "score": 0.98},
        {"tag": "brown_hair", "score": 0.91}
      ]
    }
  ]
}
```

- `tags` は score 降順。rating / character / general を区別しないフラットなリスト(danbooru タグ名は `../prompt/danbooru_tags_reference.md` の語彙と一致)
- score は 4 桁丸め

### エラー (stderr — JSON) / exit code

- `0` = 成功 / `1` = エラー
- エラー時は stderr に `{"error": "...", "details": {...}}`(未捕捉例外時は `type` も付与)。stdout は空

### 前処理・推論

- ONNX 経路の前処理は公式 space (`SmilingWolf/wd-tagger`) と同一: トランスパレンシーは白背景にコンポジット → 白で方形パッド → 448×448 bicubic リサイズ → **正規化なし (0-255 の生値)** → **BGR 順** → NHWC
- torch 経路 (safetensors/msgpack) は `config.json` の `pretrained_cfg` に従い /255 + `mean/std = 0.5` (NCHW) で正規化
- safetensors ロードは `timm.create_model('eva02_large_patch14_448', num_classes=len(tags), pretrained=False)` + `safetensors.torch.load_file` + `load_state_dict(strict=True)`。`pretrained=<ローカルパス>` は registry のデフォルト pretrained を HF から再 DL し、strict=False のため head 不一致を黙って許容する (全スコアが ≈0.5 になる) ため使わない
- ONNX の入力・出力名は実行時にメタデータから動的取得するため、モデル側の名前付けに依存しない
- ONNX 出力が [0,1] 範囲(=sigmoid 済み)と判定できたらそのまま、logits のままだと判定したら sigmoid を適用
- CSV の行順がモデルのクラスインデックスに対応 (モデルのクラス数と CSV 行数が一致すること: 新 16473 / 旧 10861)。新 CSV に存在するカテゴリは 9 (rating 4 タグ) / 0 (general 11601) / 4 (character 4868) のみ — **character は category 4** (公式コードと同じ扱い)

## custom tool 化時の環境変数

スクリプトを単一ファイルで持ち出す場合、モデルと tag CSV は環境変数で指す:

- `TAGGER_MODEL` — モデルファイルの絶対パス
- `TAGGER_TAGS` — tag 一覧 CSV の絶対パス

## ECA custom tool 登録 (`customTools.tagger`)

ECA の設定ファイル `customTools` に `tagger` として登録済みで、tool 名は `eca__tagger` で呼ばれる。command の骨格は以下のとおり（スクリプトとインタプリタの絶対パスは環境の実態に合わせて記述する。ここには書かない）:

```json
"command": "<python> <tools>/tagger.py {{images}} --threshold \"{{threshold}}\" --limit \"{{limit}}\""
```

- schema の required は `images` / `threshold` / `limit` の 3 つ（danbooru-tags と同じ設計）。`threshold` は number (0-1)、`limit` は integer で、**空文字・省略は不可**（空文字が来ると `--threshold ""` が argparse の型エラー `invalid float value: ''` になるため、shell 側の補完ではなく schema 側で必須にして防ぐ）。典型的な値として `threshold: 0.35`（スクリプト既定）と `limit: 20` を渡す運用。無制限が欲しい場合は `limit: 0`
- `images` は空白区切りの各トークンをそのまま渡す（`{{images}}` は引用符なしで展開される前提）。**1つの引用符で囲んだ複数パス文字列は渡さない**（tagger.py に 1 引数として渡り、結果が 1 要素の glob 指定として扱われてエラーになる）。パスにスペースを含めない
  - 素のファイルパス / ディレクトリパスは常に安全（ディレクトリは中の画像に展開され、他の指定と重なっても重複除去される。存在しないファイルを渡すと `一部の画像ファイルが存在しません` + `details.missing`）
  - glob を渡すのは **glob を混ぜない単独指定のときだけ**にする。混在させると失敗する可能性がある: スクリプトは `*?[` を含む引数をカレントディレクトリ基準 (`Path.cwd().glob()`) で解決するため、カレントとパターンが別のドライブ/絶対指定だと Windows の pathlib が `NotImplementedError: Non-relative patterns are unsupported` で弾く（実測: 素のパス + 同ディレクトリの glob を同時に渡すと素のパス側が解決されずこのエラーになる。同じ_drive_上で完結する glob 単独指定、およびディレクトリ指定は動作確認済み）
- 実行は ECA の tool 用シェル（設定ファイルの `toolCall` のシェル指定。config に別のシェルが指定されていればそれに従う）を介して行われる。そこで解決される `python` / `python3` が向くグローバル Python に tagger の依存（torch / timm / safetensors / Pillow / numpy）が揃っていれば動く。本ドキュメントの「依存関係」節に書いた特定バージョン・特定インストール先は開発環境の話であり、tool 実行環境とは限らない（前節の「グローバル Python で管理」は venv に固定しないという方針の話であって、パスの指定ではない）
- CPU 推論は 1 画像で数十秒オーダー。tool call の承認ダイアログが出る（承認設定の allow に `eca__tagger` を追加すれば無確認で実行できる）

## 設計判断の記録

- **safetensors を第一形式にした理由**: 将来のモデル更新が safetensors 配布のみであるため、既定の解決順も safetensors 優先。旧 ONNX ファイル (10861 クラス) は互換のため残す (16473 クラスの新モデルには行数列数が合わない)。
- **ONNX 経路を残す理由**: `onnxruntime` のみの軽量依存で、CPU 推論速度も十分。旧 `model.onnx` を `.bak` CSV とペアリングして使う想定。
- **GPU は当面 CPU 推論**: 環境は AMD RX 7900 XTX だが公式 torch には native Windows ROCm がない。GPU が欲しい場合は `onnxruntime-directml` (DirectML) を導入して ONNX 経路を速くするのが現実的な選択肢 (`--device gpu` は現状 CUDAExecutionProvider のみを試行)。
- **msgpack は第三形式**: 本モデルの公式形式だが、ロードには torch 系が必要で新規利用の利得が低い。将来の互換のため残している。
- **tag 一覧はモデルに同梱せず CSV 前提**: HF リポジトリの `selected_tags.csv` が唯一の権威であり、行順がクラスインデックスと一致している。
- **グローバル Python 前提**: 最終的に custom tool として他環境でも使われるため venv に固定せず、必須依存はグローバル環境に備える方針。

## テスト

```
D:\Python311\python -m pytest tagger\tests
```

- フィルタリングロジック(境界値含む)・JSON スキーマ・エラー経路は常時実行
- E2E(実モデル推論 + ground truth 画像との突き合わせ)は `models/` にモデルと CSV が揃っている場合のみ実行

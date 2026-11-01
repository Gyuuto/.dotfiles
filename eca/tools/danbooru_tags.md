# danbooru_tags — Danbooru タグ利用状況分析・実在チェック CLI

アニメ画像生成プロンプト作成支援ツール。`danbooru.donmai.us` の `posts.json` API を叩いて、
(1) 指定タグの**共起タグ分布**（キャラ/作品/概念の語彙のモデル実地正解）を報告する「分析モード」、
(2) 正確なタグ名の**実在確認**（EXISTS / ALIAS / NOT FOUND）を行う「チェックモード」を提供する。
**LLM から ECA custom tool (`danbooru-tags`) 経由で利用することを想定**しており、
stdout は自己完結型の Markdown レポート、エラーは stderr に分離されています。

## ファイル構成

| ファイル | 用途 |
|---|---|
| `danbooru_tags.py` | スクリプト本体（納品物） |
| `danbooru_tags.md` | このドキュメント（仕様） |
| `tests/test_danbooru_tags.py` | 仕様に基づくオフラインテスト |

## 依存関係

- Python 標準ライブラリのみ（`urllib`, `json`, `argparse`, `collections`）。サードパーティ依存なし。
- 実行環境: グローバル Python 3.11 (`D:\Python311`)。

## CLI 契約

```
python danbooru_tags.py [tag] --limit <N> [--verify "<t1>,<t2>,..."] [--check "<n1>,<n2>,..."]
```

| 引数 | 既定 | 説明 |
|---|---|---|
| `tag` | `""` | 分析対象の Danbooru タグ（キャラ/作品/general）。スペース表記は `_` に正規化される。チェック専用実行時は空文字を渡す |
| `--limit` | (必須) | サンプリング投稿数 1〜200（分析モードのみ。チェック専用実行では無視される） |
| `--verify` | `""` | サンプル内の候補タグ共起率を検証（ADOPT/MODERATE/RARE/ABSENT）。カンマ区切り |
| `--check` | `""` | 正確なタグ名の**実在確認**リスト（カンマ区切り）。サンプリングに依存しない辞書レベル判定 |

### モード

- **分析モード**（`tag` 非空）: `posts.json?tags=<tag> rating:s order:score&limit=N` で
  最高評価 SFW 投稿をサンプリングし、共起タグ周波数テーブルを出力。
- **チェック専用モード**（`tag` 空・`--check` 非空）: 各名を `posts.json?tags=<n>&limit=3` で
  単発プローブ。**サンプリングしない**ため `--limit`/`--verify` は無視される。
- **両立**: `tag` + `--check` 同時指定で、分析レポート末尾に実在チェックセクションを追記。

### 出力（stdout — 分析モード）

```
# Danbooru Tag Analysis: <tag>

## Summary            (Population / Sampling / 各カテゴリ別 distinct タグ数 / Query)
## WARNING             (小サンプル <10 件のみ)
## General / descriptive tags (appearance, clothing, scene)   (上位40行 周波数表)
## Character tags                        (上位15行)
## Copyright / work tags               (上位15行)
## Meta tags (count / image / render)  (上位15行)
## Artist tags (generally AVOID in a character prompt)
## Candidate tag verification          (--verify 時)
## Tag existence check                 (--check 時)
```

### 出力（stdout — チェックモード）

```
# Danbooru Tag Check (existence verification)

## Summary            (Names checked: N)
## Tag existence check
- `<name>`  [EXISTS] canonical tag: ...        # 名が投稿にそのまま載っている
- `<name>`  [ALIAS] ... candidate: `a`, `b`   # 別正規名に解決（全一致投稿の共通タグを候補）
- `<name>`  [NOT FOUND] ...                    # 一致投稿なし（要不存在の強いシグナル）
- `<name>`  [ERROR] <repr>                     # 単一名のネットワークエラー（他名は継続）
```

### 判定閾値（`--verify` の verdict）

share = count / total_posts_sampled

| share | 判定 |
|---|---|
| >= 30% | `adopt` — タグとして採用 |
| 5% .. 30% | `moderate` — タグか NL か要検討 |
| < 5% / 0 | `rare` / `absent` — 自然言語推奨 |

## サンプリングモデル（分析モード）

`posts.json` は独立した `rating=` / `order=` クエリパラメータを**無視する**（経験的に確認済み）。
そのため `tags` 値に `<tag> rating:s order:score` と擬似タグとして埋め込む：

- `rating:s` → safe (SFW) 投稿のみ
- `order:score` → (up-down) スコア順（最も canonical に描かれた上位を前面化）

レポートは、返った集合が「完全センサス」か「top-N サンプル」かを明示する。

## API 挙動の実測メモ（設計判断の根拠 — 2026-09 確認）

| エンドポイント | 挙動 | 採用可否 |
|---|---|---|
| `GET /posts.json?tags=<n>&limit=1` | 存在するタグ（canonical/alias）は一致投稿を返す。存在しない名は空リスト | **採用**（実在プローブの基盤） |
| `GET /tags/<name>` (show) | **実在タグでも 404**（`blonde_hair` / `motion_blur` / `against_wall` 等で確認） | 不採用 |
| `GET /tags.json?name=<n>` / `?name_matches=<n>` | **両方ともパラメータ無視**され既定ページを返す | 不採用 |
| `POST /posts/count.json` | **404**（エンドポイント消滅） | 不採用 |
| `GET /tag_aliases.json?from=<n>` | `from=` が無視され既定ページを返す | 不採用 |

したがって「実在確認」は `posts.json?tags=<n>` の**実証的プローブ**に集約する。
canonical と alias の区別は「一致投稿自身のタグ列に名が含まれるか」で判定し、
alias の正規名候補は「全一致投稿の共通タグ集合」（`alias_candidates`、上限 12 件）として提示する。
（候補には `1girl` / `solo` のような人数タグ等も混ざるが、LLM 側が意味のある名を選ぶことを前提としている。）

### `--verify` と `--check` の役割分担（重要）

- `--verify`: 「分析タグの最高評価 SFW サンプル内にそのタグは頻出するか」— **サンプリング内共起率**。
  SFW サンプル偏りのため NSFW 中心タグ（`ahegao`, `masturbation`, `pussy_juice` 等）は
  実在でも ABSENT になりうる。
- `--check`: 「その正確な名が実投稿に解決されるか」— **辞書レベル・サンプリング非依存**。
  NOT FOUND は「存在しない（または 0 投稿の新規タグ）」の強いシグナル。
  正規綴りの確定・捏造タグの捕捉に使う。

## 設計判断の記録

- **posts.json を唯一の実在シグナルにした理由**: 上記の API 実測メモ（show / tags.json / count /
  aliases が全部不信頼）。
- **`http_get_json` を単一 HTTP シームにした理由**: テストが `monkeypatch` で完全にオフライン
  化可能になること、User-Agent・タイムアウト・エラー挙動を一箇所に集中させること。
- **チェック専用モードで `--limit` を無視した理由**: サンプリングを行わないため無意味。
  ただし CLI 契約（`--limit` 必須）を崩さず、EKA custom tool テンプレートの互換性を保つ。
- **alias 候補を「全一致投稿の共通タグ」とした理由**: alias 検索は正規タグを持つ投稿のみを
  返すため、全投稿に共通するタグが正規名の最有力候補になる。
- **`nargs="?" const="" default=""` で空値を許容する理由**: shell と ECA コマンドテンプレートが
  引用された空文字列引数を落として `--verify` / `--check` に値が欠落する場合がある。

## テスト

```
D:\Python311\python -m pytest tools\tests
```

- 全テストは `http_get_json` を monkeypatch した**オフライン**で実行（ネットワーク不要）。
- カバー範囲: `norm` / `verdict` 境界値 / `describe_population` / `render_table` /
  `count_tags` / `post_tag_set` / `alias_candidates` / `fetch`・`check_name` の URL 生成と
  エラー経路 / `render_check_section` の 3 判定 + ERROR 経路 / `main` のモード分岐・
  検証・HTTP エラー・予期せぬ応答・セMICOLON 解析。
- 最新結果: 42 passed。

#!/usr/bin/env python3
"""
tagger.py — 画像タグ付け CLI (SmilingWolf wd-eva02-large-tagger-v3 対応)

仕様: 仕様詳細は同ディレクトリの tagger.md を参照すること。

出力契約:
  - stdout: 結果 JSON のみ
      {"images": [{"file": "<path>", "tags": [{"tag": "...", "score": 0.98}]}]}
  - stderr: 診断情報 (進捗・警告) とエラー JSON ({"error": ..., "details": ...})
  - exit code: 0 = 成功 / 1 = エラー
"""

import argparse
import csv
import json
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
MODELS_DIR = SCRIPT_DIR / "models"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tga"}

# モデル形式の優先順 (同一ディレクトリ内で候補として探す順)
MODEL_CANDIDATES = ("model.safetensors", "model.onnx", "model.msgpack")
TAGS_CANDIDATES = ("selected_tags.csv",)

# selected_tags.csv の category 列 (本モデルの CSV に存在するのは 9 / 0 / 4 のみ)
# 現行 CSV (16473 行・新モデル用): general 11601 / character 4868 / rating 4
# (旧 ONNX モデル用の 10861 行 CSV: general 8106 / character 2751)
CATEGORY_GENERAL = 0
CATEGORY_RATING = 9       # 4 タグ (general/sensitive/questionable/explicit, CSV 先頭)
CATEGORY_CHARACTER = 4    # 公式コードは character を category 4 で扱う
CATEGORY_ARTIST = 2
CATEGORY_META = 3
CATEGORY_COPYRIGHT = 4

# EVA02-large tagger v3 の前処理
# - ONNX 経路: 公式 space (SmilingWolf/wd-tagger) と同一
#   (白背景コンポジット → 方形パッド → 448  resize → 正規化なし → BGR → NHWC)
# - torch 経路: config.json の pretrained_cfg に従い /255 + mean/std 0.5 (NCHW)
IMG_SIZE = 448
MEAN = (0.5, 0.5, 0.5)
STD = (0.5, 0.5, 0.5)


def eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


def fail(message: str, details: dict | None = None) -> None:
    """stderr にエラー JSON を出力して終了 (exit code 1)。"""
    err = {"error": message}
    if details:
        err["details"] = details
    print(json.dumps(err, ensure_ascii=False), file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# パス解決
# ---------------------------------------------------------------------------

def resolve_model_path(cli_value: str | None) -> Path | None:
    """モデルファイルの解決: --model → 環境変数 TAGGER_MODEL → 既定候補。

    戻り値が None の場合、呼び出し側は「モデルが見つからない」エラーとする。
    """
    env = os.environ.get("TAGGER_MODEL")
    for candidate in (cli_value, env):
        if candidate:
            return Path(candidate)
    for name in MODEL_CANDIDATES:
        p = MODELS_DIR / name
        if p.exists():
            return p
    # フォールバック: models/ 内を拡張子で探索
    for ext in (".onnx", ".safetensors", ".msgpack"):
        hits = sorted(MODELS_DIR.glob(f"*{ext}"))
        if hits:
            return hits[0]
    return None


def resolve_tags_path(cli_value: str | None, model_path: Path) -> Path | None:
    """tag 一覧 CSV の解決: --tags → 環境変数 TAGGER_TAGS → モデルの隣接 → models/。"""
    env = os.environ.get("TAGGER_TAGS")
    candidates = []
    if cli_value:
        candidates.append(Path(cli_value))
    if env:
        candidates.append(Path(env))
    if model_path is not None:
        candidates.append(model_path.parent / "selected_tags.csv")
    for name in TAGS_CANDIDATES:
        candidates.append(MODELS_DIR / name)
    for candidate in candidates:
        if candidate and candidate.exists():
            return candidate
    return None


# ---------------------------------------------------------------------------
# tag 一覧
# ---------------------------------------------------------------------------

def load_tag_list(csv_path: Path) -> list[tuple[str, int]]:
    """selected_tags.csv を (tag名, category) のリストとして読み込む。

    CSV の行順がモデルのクラスインデックスに対応する (クラス 0 = 先頭データ行)。
    """
    tags: list[tuple[str, int]] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"name", "category"}
        if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
            fail("tag 一覧 CSV の形式が不正です",
                 {"path": str(csv_path), "fieldnames": reader.fieldnames})
        for row in reader:
            try:
                tags.append((row["name"], int(row["category"])))
            except (KeyError, ValueError):
                continue
    if not tags:
        fail("tag 一覧 CSV が空です", {"path": str(csv_path)})
    return tags


# ---------------------------------------------------------------------------
# 前処理
# ---------------------------------------------------------------------------

def _preprocess_image(image_path: Path) -> "np.ndarray":
    """単一画像を (1, H, W, 3) の float32 テンソルにする (ONNX 経路・公式仕様に従う)。

    - トランスパレンシーは白背景にコンポジット
    - 白で方形パッド (中心配置) → 448×448 に bicubic リサイズ
    - 正規化なし (0-255 の生値)・BGR 順
    """
    import numpy as np
    from PIL import Image

    img = Image.open(image_path).convert("RGBA")
    canvas = Image.new("RGBA", img.size, (255, 255, 255, 255))
    canvas.alpha_composite(img)
    img = canvas.convert("RGB")

    w, h = img.size
    max_dim = max(w, h)
    pad_left = (max_dim - w) // 2
    pad_top = (max_dim - h) // 2
    padded = Image.new("RGB", (max_dim, max_dim), (255, 255, 255))
    padded.paste(img, (pad_left, pad_top))
    if max_dim != IMG_SIZE:
        padded = padded.resize((IMG_SIZE, IMG_SIZE), Image.BICUBIC)

    arr = np.asarray(padded, dtype=np.float32)
    arr = arr[:, :, ::-1]  # RGB → BGR
    return np.expand_dims(arr, 0)


def preprocess_batch(image_paths: list[Path]) -> "np.ndarray":
    """複数画像を (N, H, W, 3) に結合する。"""
    import numpy as np

    return np.concatenate([_preprocess_image(p) for p in image_paths], axis=0)


# ---------------------------------------------------------------------------
# モデル
# ---------------------------------------------------------------------------

class ModelRunner:
    """形式ごとに推論を切り替えるラッパー。

    load_tags(csv_path) を先に呼び、get_tags() を通してタグ列を共有する。
    """

    def __init__(self) -> None:
        self.kind = "onnx"
        self.input_name: str | None = None
        self.output_names: list[str] = []
        self._session = None
        self._torch_model = None
        self.tags: list[tuple[str, int]] = []

    def load(self, model_path: Path, device: str) -> None:
        if model_path.suffix.lower() == ".onnx":
            self._load_onnx(model_path, device)
        elif model_path.suffix.lower() == ".safetensors":
            self._load_torch(model_path)
        elif model_path.suffix.lower() == ".msgpack":
            self._load_torch(model_path)
        else:
            fail("未対応のモデル形式です",
                 {"path": str(model_path), "supported": [".onnx", ".safetensors", ".msgpack"]})

    def _load_onnx(self, model_path: Path, device: str) -> None:
        try:
            import onnxruntime as ort
        except ImportError:
            fail("onnxruntime がインストールされていません",
                 {"hint": "pip install 'onnxruntime>=1.17.0'"})
        providers = ["CPUExecutionProvider"]
        if device == "gpu":
            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
            eprint("[tagger] GPU 推論を試行中 (CUDAExecutionProvider)")
        try:
            self._session = ort.InferenceSession(
                str(model_path), providers=providers,
            )
        except Exception as e:  # noqa: BLE001
            if device == "gpu":
                eprint(f"[tagger] GPU 初期化に失敗 ({e}) — CPU にフォールバックします")
                self._session = ort.InferenceSession(str(model_path))
            else:
                fail("ONNX モデルのロードに失敗しました",
                     {"path": str(model_path), "detail": str(e)})
        self.kind = "onnx"
        self.input_name = self._session.get_inputs()[0].name
        self.output_names = [o.name for o in self._session.get_outputs()]
        eprint(f"[tagger] ONNX 入力: {self.input_name} / 出力: {self.output_names}")

    def _load_torch(self, model_path: Path) -> None:
        try:
            import timm
            import torch
        except ImportError as e:
            fail("torch / timm がインストールされていません (safetensors/msgpack 形式用)",
                 {"detail": str(e), "hint": "pip install torch timm"})
        arch = "eva02_large_patch14_448"
        num_classes = len(self.tags)
        try:
            if model_path.suffix.lower() == ".safetensors":
                import safetensors.torch
                # pretrained=パス指定は registry のデフォルト pretrained を
                # HF から再 DL し、strict=False で head が黙って不一致になる
                # ため、手動 strict-load する
                model = timm.create_model(
                    arch, num_classes=num_classes, pretrained=False,
                )
                state = safetensors.torch.load_file(str(model_path))
                model.load_state_dict(state, strict=True)
                self._torch_model = model
            else:  # .msgpack
                state = torch.load(str(model_path), map_location="cpu", weights_only=False)
                model = timm.create_model(arch, num_classes=num_classes)
                model.load_state_dict(state)
                self._torch_model = model
        except Exception as e:  # noqa: BLE001
            fail("モデルのロードに失敗しました",
                 {"path": str(model_path), "detail": str(e)})
        self._torch_model.eval()
        self.kind = "torch"

    def load_tags(self, csv_path: Path) -> None:
        self.tags = load_tag_list(csv_path)

    def get_tags(self) -> list[tuple[str, int]]:
        return self.tags

    def run(self, batch: "np.ndarray") -> "np.ndarray":
        """バッチ推論。戻り値: (N, num_classes) の float32 スコア。"""
        import numpy as np

        if self.kind == "onnx":
            outs = self._session.run(None, {self.input_name: batch})
            # 単一出力 → そのまま; 複数出力 → 最初の (main) 出力を使う
            out = np.asarray(outs[0], dtype=np.float32)
            if out.ndim == 3:
                out = out.reshape(len(out), -1)
            return out
        # torch: NHWC → NCHW に変換し、/255 + mean/std 0.5 で正規化 (config.json 準拠)
        import torch

        x = torch.from_numpy(batch).permute(0, 3, 1, 2).float()
        x = (x / 255.0 - 0.5) / 0.5
        with torch.no_grad():
            logits = self._torch_model(x)
        return torch.sigmoid(logits).numpy().astype(np.float32)


def _postprocess_scores(scores: "np.ndarray") -> "np.ndarray":
    """ONNX 出力に sigmoid が未適用だった場合 (logits のまま) を補正する。

    値の範囲で判定: 既に [0, 1] に収まっていればそのまま、
    1 超または 0 未満の値が混ざっていれば sigmoid を適用する。
    """
    import numpy as np

    if scores.size == 0:
        return scores
    if scores.max() <= 1.0 + 1e-6 and scores.min() >= -1e-6:
        return np.clip(scores, 0.0, 1.0)
    return 1.0 / (1.0 + np.exp(-scores.astype(np.float64)))


def filter_tags(
    scores: "np.ndarray",
    tags: list[tuple[str, int]],
    threshold: float,
    limit: int,
) -> list[dict]:
    """スコアとタグを対応させ、threshold / limit を適用して降順リストを返す。

    scores: (num_classes,) の 1 画像分の配列 (または (1, num_classes))
    戻り値: [{"tag": ..., "score": ...}, ...]
    """
    import numpy as np

    s = np.asarray(scores, dtype=np.float64).reshape(-1)
    if s.size != len(tags):
        fail("モデル出力サイズと tag 一覧の行数が一致しません",
             {"model_outputs": int(s.size), "tag_list": len(tags)})
    # 4 桁丸めしてから閾値判定する (float32 による 0.35 の下振れを吸収)
    pairs = []
    for (tag, _cat), score in zip(tags, s):
        sc = round(float(score), 4)
        if sc >= threshold:
            pairs.append({"tag": tag, "score": sc})
    pairs.sort(key=lambda x: x["score"], reverse=True)
    if limit:  # 0 = 無制限
        pairs = pairs[:limit]
    return pairs


# ---------------------------------------------------------------------------
# 画像収集
# ---------------------------------------------------------------------------

def collect_images(paths: list[str]) -> list[Path]:
    """ファイル/ディレクトリ/ワイルドカードのリストを画像ファイルリストに展開。"""
    collected: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            for ext in IMAGE_EXTS:
                collected.extend(sorted(p.glob(f"*{ext}")))
                collected.extend(sorted(p.glob(f"*{ext.upper()}")))
        elif any(ch in raw for ch in "*?["):
            collected.extend(sorted(Path.cwd().glob(raw)))
        else:
            collected.append(p)
    # 重複除去 (順序保持)
    seen: set[Path] = set()
    unique: list[Path] = []
    for item in collected:
        key = item.resolve()
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="画像を danbooru タグでタグ付け (wd-eva02-large-tagger-v3)",
    )
    parser.add_argument("images", nargs="+",
                        help="画像ファイル、ディレクトリ、または glob (複数可)")
    parser.add_argument("--model", default=None,
                        help="モデルファイルパス "
                             "(既定: 環境変数 TAGGER_MODEL → scripts/隣の models/ 内候補)")
    parser.add_argument("--tags", default=None,
                        help="tag 一覧 CSV パス "
                             "(既定: 環境変数 TAGGER_TAGS → モデル隣接の selected_tags.csv)")
    parser.add_argument("--threshold", type=float, default=0.35,
                        help="スコア下限 (既定 0.35)")
    parser.add_argument("--limit", type=int, default=20,
                        help="画像ごとのタグ数上限 (既定 20, 0 で無制限)")
    parser.add_argument("--device", choices=["cpu", "gpu"], default="cpu",
                        help="推論デバイス (gpu は CUDA 対応 onnxruntime が必要)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    # stdout を UTF-8 に固定 (Windows の cp932 デフォルト対策)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    args = parse_args(argv)

    model_path = resolve_model_path(args.model)
    if model_path is None or not Path(model_path).exists():
        fail("モデルファイルが見つかりません",
             {"model_path": str(model_path),
              "searched": [str(MODELS_DIR / n) for n in MODEL_CANDIDATES]})
    tags_path = resolve_tags_path(args.tags, Path(model_path))
    if tags_path is None:
        fail("tag 一覧 CSV (selected_tags.csv) が見つかりません",
             {"model_dir": str(Path(model_path).parent)})

    images = collect_images(args.images)
    if not images:
        fail("対象の画像が見つかりませんでした", {"inputs": args.images})
    missing = [str(p) for p in images if not p.exists()]
    if missing:
        fail("一部の画像ファイルが存在しません", {"missing": missing})

    eprint(f"[tagger] {len(images)} 件の画像を処理します (model: {model_path})")

    runner = ModelRunner()
    runner.load_tags(tags_path)  # torch 系はクラス数に必要
    runner.load(model_path, args.device)

    scores = runner.run(preprocess_batch(images))
    scores = _postprocess_scores(scores)
    tags = runner.get_tags()

    results = []
    for path, row in zip(images, scores):
        results.append({
            "file": str(path),
            "tags": filter_tags(row, tags, args.threshold, args.limit),
        })

    print(json.dumps({"images": results}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"error": str(e), "type": type(e).__name__},
                        ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

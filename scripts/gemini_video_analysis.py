#!/usr/bin/env python3
"""
CiviLink オンボーディング ユーザビリティ解析スクリプト（方式C）

Step 1: トランスクリプト（Geminiメモ等）をテキスト分析 → WF分類・摩擦箇所・感情反応を抽出
Step 2: 摩擦箇所のみ動画APIで視覚確認 → マウス操作・UI状態の裏付け
Step 3: 統合レポート＋改善提案を出力

使い方:
  # 基本（トランスクリプト＋動画で完全解析）
  python3 scripts/gemini_video_analysis.py \\
    --transcript path/to/transcript.md \\
    --video path/to/video.mp4 \\
    --output path/to/report.md

  # トランスクリプトのみ（動画なし）
  python3 scripts/gemini_video_analysis.py \\
    --transcript path/to/transcript.md \\
    --output path/to/report.md

  # アップロード済み動画を再利用
  python3 scripts/gemini_video_analysis.py \\
    --transcript path/to/transcript.md \\
    --file-id files/xxxxx \\
    --output path/to/report.md

  # タスク定義付きで解析（再現性向上）
  python3 scripts/gemini_video_analysis.py \\
    --transcript path/to/transcript.md \\
    --video path/to/video.mp4 \\
    --tasks path/to/tasks.json \\
    --customer "クロスプランニング様" \\
    --output path/to/report.md

環境変数:
  GOOGLE_API_KEY: Google AI Studio APIキー（.envファイルでも可）

依存パッケージ:
  pip3 install google-genai python-dotenv
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types


# ============================================================
# Step 1: トランスクリプト分析用プロンプト
# ============================================================

PROMPT_STEP1 = """あなたはUXリサーチャーです。以下はオンボーディングセッション（{product_name}）のトランスクリプト（文字起こし）です。

## 顧客情報
- 顧客: {customer}
{tasks_section}
## 分析タスク

このトランスクリプトを読み、以下を**厳密にJSON形式で**出力してください。

### 出力フォーマット（JSON）

```json
{{
  "session_overview": {{
    "duration_min": 90,
    "participants": ["参加者1（役割）", "参加者2（役割）"],
    "session_phases": [
      {{"phase": "前半", "time_range": "00:00:00〜00:20:00", "description": "概要"}}
    ]
  }},
  "workflows": [
    {{
      "id": "WF-01",
      "name": "ワークフロー名",
      "task_id": "対応するタスク定義のID（tasks_definitionがある場合）。なければnull",
      "time_range": "00:00:00〜00:05:00",
      "start_sec": 0,
      "end_sec": 300,
      "operator": "操作者名",
      "ideal_path": ["理想的な操作手順1", "理想的な操作手順2"],
      "actual_path": ["実際に行った操作1", "実際に行った操作2"],
      "task_completed": true,
      "task_completed_independently": false,
      "abcd": "B",
      "abcd_reason": "分類の根拠（具体的な発言やタイムスタンプを引用）",
      "friction_points": [
        {{
          "timestamp": "00:02:30",
          "timestamp_sec": 150,
          "description": "摩擦の内容",
          "severity": "high",
          "evidence": "具体的な発言引用",
          "needs_video_check": true,
          "video_check_reason": "マウスの動きを確認したい"
        }}
      ],
      "positive_reactions": [
        {{
          "timestamp": "00:03:00",
          "quote": "「おー、すごい」",
          "value_recognized": "差分比較"
        }}
      ],
      "negative_reactions": [
        {{
          "timestamp": "00:02:30",
          "quote": "「これどうするの？」",
          "issue": "操作方法がわからない"
        }}
      ],
      "improvement_proposals": [
        "改善提案1",
        "改善提案2"
      ]
    }}
  ],
  "user_requests": [
    {{
      "timestamp": "00:45:00",
      "content": "iPadで使いたい",
      "category": "iPad対応"
    }}
  ],
  "video_check_segments": [
    {{
      "start_sec": 120,
      "end_sec": 180,
      "reason": "D&D操作の失敗回数と具体的なマウス軌跡を確認",
      "related_wf": "WF-08",
      "priority": "high"
    }}
  ],
  "overall_impression": {{
    "adoption_willingness": "high/medium/low",
    "key_value_recognized": ["差分比較", "メール通知"],
    "key_concerns": ["iPad未対応", "操作の複雑さ"]
  }}
}}
```

### 分類基準（ABCD）— 以下の基準を厳密に適用すること

**A. 価値未到達**（以下のいずれかに該当）:
- タスクを完了できなかった（リサーチャーの介入が必要だった）
- 機能が動作しなかった（バグ・機能不全）
- ユーザーが機能の価値・目的を理解できなかった

**B. 認知摩擦あり**（以下のいずれかに該当）:
- タスクは完了したが、独力での再現が危うい（ヒントや説明が必要だった）
- 正しい操作にたどり着くまでに3回以上の試行錯誤があった
- 「どこ？」「これ？」「分からない」等の発言があった

**C. 表現要改善**（以下のいずれかに該当）:
- タスクは独力で完了したが、迷いや一瞬の戸惑いがあった
- UIラベル・色・配置に改善の余地がある指摘があった
- 理解はしたが「〜の方がいい」等の改善要望が出た

**D. 問題なし**:
- タスクを独力でスムーズに完了。迷いなし

**重要**: ガイド付きの操作（リサーチャーが指示した上での操作）はDに分類しないこと。「独力で完了できたか」を常に判断基準とする。

### `needs_video_check` を true にすべきケース
- ドラッグ&ドロップの操作（成否が発言だけでは判断できない）
- マウスが迷っている可能性がある箇所（「どこだ」「これかな」等の発言）
- UIの視認性問題（小さいボタン、アイコンの発見しにくさ）
- 操作ミスの具体的回数の確認

### `needs_video_check` を false にできるケース
- 発言から明確に状況がわかるもの（「あ、送信してないからか」等）
- 質問・感情反応（「すごい」「iPadで使いたい」等）
- 概念理解の摩擦（保存と送信の違い等）

**JSONのみを出力してください。説明文は不要です。**

---

## トランスクリプト

{transcript}
"""


# ============================================================
# Step 2: 動画検証用プロンプト
# ============================================================

PROMPT_STEP2_SEGMENT = """あなたはUXリサーチャーです。この動画は{product_name}のオンボーディングセッションの{time_range}部分です。

## 検証タスク

トランスクリプト分析で以下の摩擦ポイントが特定されました。動画を見て**視覚的に検証**してください。

{check_items}

## 検証観点
各摩擦ポイントについて：
1. マウスカーソルの動き（止まった秒数、探し回った範囲）
2. クリックの正確さ（正しい場所をクリックしたか、何回ミスしたか）
3. UI要素の視認性（ボタンのサイズ、位置、ラベルの明確さ）
4. ドラッグ&ドロップの成否（何回試行したか）
5. トランスクリプト分析の分類（ABCD）が妥当かどうか

## 出力フォーマット（JSON）

```json
{{
  "verifications": [
    {{
      "related_wf": "WF-08",
      "original_severity": "high",
      "verified_severity": "high",
      "abcd_update": null,
      "findings": "5回連続でD&D失敗。22:31, 22:38, 22:50, 23:09, 23:17。すべてPDFがブラウザで開く",
      "mouse_behavior": "ファイルリストの異なる要素（チェックボックス、アイコン、ファイル名）を往復",
      "additional_friction": "22:44に「変更後を変更前に重ねてもいい？」と上書き概念の不理解も確認",
      "ui_observations": "ドロップゾーンの視覚的表示なし。ドラッグ中のハイライトフィードバックなし"
    }}
  ]
}}
```

**JSONのみを出力してください。**"""


# ============================================================
# Step 3: 最終レポート生成用プロンプト
# ============================================================

PROMPT_STEP3_REPORT = """以下は{product_name}のオンボーディングセッション（{customer}）のユーザビリティテスト分析データです。

## トランスクリプト分析結果
```json
{step1_json}
```

## 動画検証結果
{step2_section}

---

上記データを統合して、**日本語で**最終レポートを作成してください。

## 出力フォーマット

# ユーザビリティテスト分析: {customer} オンボーディング

## テスト概要
| 項目 | 内容 |
|---|---|
| 顧客 | {customer} |
| セッション時間 | （データから） |
| 参加者 | （データから） |
| 分析手法 | トランスクリプト分析{analysis_method_suffix} |

## エグゼクティブサマリー

### ABCD分類一覧
| WF | ワークフロー | 分類 | 信頼度 | 根拠 |
|---|---|---|---|---|
（動画検証済みは信頼度「高」、未検証は「中」）

### 最重要改善ポイント（TOP 3）
（横断的な問題を特定し、影響範囲の広い順に）

## ワークフロー別詳細分析
（各WFについて: 理想パス、実際の動線、摩擦ポイント、感情反応、改善提案）

## 摩擦ポイント一覧（重要度順）
| タイムスタンプ | 内容 | WF | 重要度 | 動画確認 |
|---|---|---|---|---|

## ポジティブ反応ハイライト
| タイムスタンプ | 発言 | 価値認識 |
|---|---|---|

## ユーザー要望
| タイムスタンプ | 内容 | カテゴリ |
|---|---|---|

## 改善ロードマップ
### 即時対応（Sprint 1）
### 短期対応（1-2 Sprint）
### 中期対応（3-6 Sprint）

## 導入意欲の評価

## 分析の限界と注記
"""


# ============================================================
# ユーティリティ関数
# ============================================================

def load_api_key(env_path: Optional[str] = None) -> str:
    """APIキーを環境変数または.envから読み込む"""
    if env_path:
        load_dotenv(env_path, override=True)
    else:
        project_root = Path(__file__).resolve().parent.parent
        env_file = project_root / ".env"
        if env_file.exists():
            load_dotenv(env_file, override=True)

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("エラー: GOOGLE_API_KEY が設定されていません", file=sys.stderr)
        print("  export GOOGLE_API_KEY=your-key  または .env に記載してください", file=sys.stderr)
        sys.exit(1)
    return api_key


def ensure_ascii_path(path: Path) -> Path:
    """日本語ファイル名の場合、ASCII名のシンボリックリンクを作成"""
    try:
        str(path.name).encode("ascii")
        return path
    except UnicodeEncodeError:
        link_path = path.parent / f"_upload_temp{path.suffix}"
        if link_path.exists():
            link_path.unlink()
        os.symlink(path, link_path)
        print(f"  ASCII名リンク作成: {link_path.name}")
        return link_path


def upload_video(client: genai.Client, video_path: str) -> str:
    """動画をGemini Files APIにアップロードし、処理完了を待つ"""
    path = Path(video_path).resolve()
    if not path.exists():
        print(f"エラー: ファイルが見つかりません: {video_path}", file=sys.stderr)
        sys.exit(1)

    size_mb = path.stat().st_size / (1024 * 1024)
    print(f"動画アップロード開始... ({size_mb:.0f}MB)")

    upload_path = ensure_ascii_path(path)
    video_file = client.files.upload(file=str(upload_path))
    print(f"  アップロード完了: {video_file.name}")

    # 一時リンクを削除
    if upload_path != path and upload_path.name.startswith("_upload_temp"):
        upload_path.unlink()

    # 処理完了を待つ
    while video_file.state.name == "PROCESSING":
        print(f"  処理中...")
        time.sleep(10)
        video_file = client.files.get(name=video_file.name)

    if video_file.state.name == "FAILED":
        print(f"エラー: 動画の処理に失敗しました", file=sys.stderr)
        sys.exit(1)

    print(f"  準備完了: {video_file.name}")
    return video_file.name


def format_time(seconds: int) -> str:
    """秒数をMM:SS形式に変換"""
    m, s = divmod(seconds, 60)
    return f"{m:02d}:{s:02d}"


def extract_json(text: str) -> dict:
    """Geminiの応答からJSONを抽出する"""
    # ```json ... ``` ブロックを探す
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    # ブロックがなければ全体をパース
    # 先頭/末尾の非JSON文字を除去
    text = text.strip()
    if text.startswith("{"):
        return json.loads(text)
    raise ValueError(f"JSONを抽出できません: {text[:200]}...")


def call_gemini(
    client: genai.Client,
    prompt: str,
    model: str = "gemini-2.5-flash",
    video_part: Optional[types.Part] = None,
    max_retries: int = 2,
) -> str:
    """Gemini APIを呼び出す。リトライ付き"""
    for attempt in range(max_retries + 1):
        try:
            if video_part:
                response = client.models.generate_content(
                    model=model,
                    contents=[
                        types.Content(
                            parts=[video_part, types.Part.from_text(text=prompt)]
                        )
                    ],
                )
            else:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                )
            return response.text
        except Exception as e:
            if attempt < max_retries:
                wait = 10 * (attempt + 1)
                print(f"  リトライ ({attempt + 1}/{max_retries}): {wait}秒待機... ({e})")
                time.sleep(wait)
            else:
                raise


# ============================================================
# Step 1: トランスクリプト分析
# ============================================================

def load_tasks(tasks_path: Optional[str]) -> Optional[dict]:
    """タスク定義JSONを読み込む"""
    if not tasks_path:
        return None
    path = Path(tasks_path)
    if not path.exists():
        print(f"  警告: タスク定義ファイルが見つかりません: {tasks_path}", file=sys.stderr)
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_tasks_section(tasks: Optional[dict]) -> str:
    """タスク定義からプロンプト用のセクションを構築"""
    if not tasks:
        return ""

    lines = ["\n## タスク定義（テストシナリオ）\n"]
    lines.append("以下はテスト実施者に事前に指示されたタスク内容です。")
    lines.append("各ワークフローは以下のタスクに対応付けて分析してください。")
    lines.append("「理想パス」はこのタスク定義から導出し、「実際の動線」と比較してください。\n")

    # テスター情報
    testers = tasks.get("testers", [])
    if testers:
        lines.append("### テスター")
        for t in testers:
            role = t.get("role", "")
            name = t.get("name", "不明")
            lines.append(f"- **{name}**（{role}）")
        lines.append("")

    # タスク一覧
    task_list = tasks.get("tasks", [])
    if task_list:
        lines.append("### タスク一覧")
        for task in task_list:
            tid = task.get("id", "?")
            name = task.get("name", "")
            tester = task.get("tester", "")
            steps = task.get("expected_steps", [])
            lines.append(f"\n**{tid}: {name}**（操作者: {tester}）")
            if task.get("description"):
                lines.append(f"  説明: {task['description']}")
            if steps:
                lines.append("  理想的な操作手順:")
                for i, step in enumerate(steps, 1):
                    lines.append(f"    {i}. {step}")
        lines.append("")

    # セッション全体の条件
    conditions = tasks.get("conditions", {})
    if conditions:
        lines.append("### テスト条件")
        if conditions.get("guided"):
            lines.append(f"- ガイド: {conditions['guided']}")
        if conditions.get("environment"):
            lines.append(f"- 環境: {conditions['environment']}")
        if conditions.get("notes"):
            lines.append(f"- 備考: {conditions['notes']}")
        lines.append("")

    return "\n".join(lines)


def step1_transcript_analysis(
    client: genai.Client,
    transcript_path: str,
    product_name: str,
    customer: str,
    model: str,
    tasks: Optional[dict] = None,
) -> dict:
    """トランスクリプトを分析してWF分類・摩擦箇所を抽出"""
    print("\n" + "=" * 60)
    print("Step 1: トランスクリプト分析")
    print("=" * 60)

    transcript = Path(transcript_path).read_text(encoding="utf-8")
    print(f"  トランスクリプト: {len(transcript)}文字")

    tasks_section = build_tasks_section(tasks)
    if tasks_section:
        task_count = len(tasks.get("tasks", []))
        tester_count = len(tasks.get("testers", []))
        print(f"  タスク定義: {task_count}タスク, {tester_count}テスター")

    prompt = PROMPT_STEP1.format(
        product_name=product_name,
        customer=customer,
        tasks_section=tasks_section,
        transcript=transcript,
    )

    print("  Geminiで分析中...")
    response_text = call_gemini(client, prompt, model)
    print(f"  応答: {len(response_text)}文字")

    result = extract_json(response_text)

    # サマリー表示
    wfs = result.get("workflows", [])
    checks = result.get("video_check_segments", [])
    print(f"\n  検出ワークフロー: {len(wfs)}件")
    for wf in wfs:
        friction_count = len(wf.get("friction_points", []))
        video_needed = sum(1 for fp in wf.get("friction_points", []) if fp.get("needs_video_check"))
        print(f"    {wf['id']} {wf['name']}: {wf['abcd']} (摩擦{friction_count}件, 動画確認{video_needed}件)")
    print(f"  動画確認セグメント: {len(checks)}件")
    for seg in checks:
        print(f"    [{seg.get('priority', '?')}] {format_time(seg['start_sec'])}-{format_time(seg['end_sec'])}: {seg['reason']}")

    return result


# ============================================================
# Step 2: 動画による摩擦箇所の検証
# ============================================================

def step2_video_verification(
    client: genai.Client,
    file_id: str,
    step1_result: dict,
    product_name: str,
    model: str,
) -> list:
    """Step 1で特定された摩擦箇所を動画で視覚的に検証"""
    segments = step1_result.get("video_check_segments", [])
    if not segments:
        print("\n  動画確認が必要なセグメントはありません。")
        return []

    # priority でソートして high から処理
    segments.sort(key=lambda s: PRIORITY_ORDER.get(s.get("priority", "low"), 3))

    print(f"\n{'=' * 60}")
    print(f"Step 2: 動画検証 ({len(segments)}セグメント)")
    print("=" * 60)

    video_file = client.files.get(name=file_id)
    all_verifications = []

    # 近接セグメントをマージ（30秒以内の間隔は結合）
    merged = _merge_segments(segments)
    print(f"  マージ後: {len(merged)}セグメント")

    for i, seg in enumerate(merged):
        start = seg["start_sec"]
        end = seg["end_sec"]
        # 前後に30秒のバッファを追加（文脈理解のため）
        buffered_start = max(0, start - 30)
        buffered_end = end + 30

        label = f"検証 {i + 1}/{len(merged)}"
        print(f"\n  {label}: {format_time(buffered_start)}-{format_time(buffered_end)}")
        print(f"    対象WF: {', '.join(seg.get('related_wfs', [seg.get('related_wf', '?')]))}")
        print(f"    理由: {seg['reason']}")

        # 確認項目をテキスト化
        check_items = []
        for reason in seg.get("reasons", [seg["reason"]]):
            check_items.append(f"- {reason}")
        check_text = "\n".join(check_items)

        time_range = f"{format_time(buffered_start)}〜{format_time(buffered_end)}"
        prompt = PROMPT_STEP2_SEGMENT.format(
            product_name=product_name,
            time_range=time_range,
            check_items=check_text,
        )

        video_part = types.Part(
            file_data=types.FileData(file_uri=video_file.uri, mime_type="video/mp4"),
            video_metadata=types.VideoMetadata(
                startOffset=f"{buffered_start}s",
                endOffset=f"{buffered_end}s",
            ),
        )

        try:
            response_text = call_gemini(client, prompt, model, video_part=video_part)
            result = extract_json(response_text)
            verifications = result.get("verifications", [])
            all_verifications.extend(verifications)
            print(f"    完了: {len(verifications)}件の検証結果")
        except Exception as e:
            print(f"    エラー: {e}", file=sys.stderr)
            all_verifications.append({
                "related_wf": seg.get("related_wf", "?"),
                "findings": f"動画検証エラー: {e}",
                "verified_severity": "unknown",
            })

    return all_verifications


MAX_CLIP_DURATION = 600  # マージ後のクリップ上限（秒）。超えると分割
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _merge_segments(segments: list) -> list:
    """近接するセグメント（30秒以内）をマージ。上限超過時は分割"""
    if not segments:
        return []

    sorted_segs = sorted(segments, key=lambda s: s["start_sec"])
    merged = [dict(sorted_segs[0])]
    merged[0].setdefault("reasons", [merged[0]["reason"]])
    merged[0].setdefault("related_wfs", [merged[0].get("related_wf", "?")])

    for seg in sorted_segs[1:]:
        last = merged[-1]
        potential_end = max(last["end_sec"], seg["end_sec"])
        potential_duration = potential_end - last["start_sec"]

        if seg["start_sec"] <= last["end_sec"] + 30 and potential_duration <= MAX_CLIP_DURATION:
            # マージ
            last["end_sec"] = potential_end
            last["reasons"].append(seg["reason"])
            wf = seg.get("related_wf", "?")
            if wf not in last["related_wfs"]:
                last["related_wfs"].append(wf)
            # priority は最も高いものを採用
            if PRIORITY_ORDER.get(seg.get("priority", "low"), 3) < PRIORITY_ORDER.get(last.get("priority", "low"), 3):
                last["priority"] = seg["priority"]
        else:
            new_seg = dict(seg)
            new_seg.setdefault("reasons", [seg["reason"]])
            new_seg.setdefault("related_wfs", [seg.get("related_wf", "?")])
            merged.append(new_seg)

    return merged


# ============================================================
# Step 3: 最終レポート生成
# ============================================================

def step3_generate_report(
    client: genai.Client,
    step1_result: dict,
    step2_verifications: list,
    product_name: str,
    customer: str,
    model: str,
    output_path: str,
) -> None:
    """Step 1+2の結果を統合して最終レポートを生成"""
    print(f"\n{'=' * 60}")
    print("Step 3: 最終レポート生成")
    print("=" * 60)

    step1_json = json.dumps(step1_result, ensure_ascii=False, indent=2)

    if step2_verifications:
        step2_json = json.dumps(step2_verifications, ensure_ascii=False, indent=2)
        step2_section = f"```json\n{step2_json}\n```"
        method_suffix = " + Gemini動画検証"
    else:
        step2_section = "（動画検証なし — トランスクリプトのみの分析）"
        method_suffix = ""

    prompt = PROMPT_STEP3_REPORT.format(
        product_name=product_name,
        customer=customer,
        step1_json=step1_json,
        step2_section=step2_section,
        analysis_method_suffix=method_suffix,
    )

    print("  レポート生成中...")
    response_text = call_gemini(client, prompt, model)
    print(f"  応答: {len(response_text)}文字")

    # ファイル書き出し
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(response_text)
        f.write("\n\n---\n\n")
        f.write("## 分析メタデータ\n\n")
        f.write(f"| 項目 | 内容 |\n|---|---|\n")
        f.write(f"| 解析日時 | {time.strftime('%Y-%m-%d %H:%M')} |\n")
        f.write(f"| モデル | {model} |\n")
        f.write(f"| 方式 | C（トランスクリプト先行 + 動画スポット検証） |\n")
        f.write(f"| WF数 | {len(step1_result.get('workflows', []))} |\n")
        f.write(f"| 動画検証数 | {len(step2_verifications)} |\n")

    # 中間データも保存
    intermediate_path = Path(output_path).with_suffix(".intermediate.json")
    with open(intermediate_path, "w", encoding="utf-8") as f:
        json.dump({
            "step1": step1_result,
            "step2_verifications": step2_verifications,
            "metadata": {
                "product_name": product_name,
                "customer": customer,
                "model": model,
                "timestamp": time.strftime("%Y-%m-%d %H:%M"),
            },
        }, f, ensure_ascii=False, indent=2)

    print(f"\n  レポート: {output_path}")
    print(f"  中間データ: {intermediate_path}")


# ============================================================
# メイン
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="CiviLink ユーザビリティ解析（方式C: トランスクリプト先行 + 動画スポット検証）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 基本（トランスクリプト＋動画）
  python3 scripts/gemini_video_analysis.py \\
    --transcript civilink-movie/transcript.md \\
    --video civilink-movie/video.mp4 \\
    -o civilink-movie/report.md

  # トランスクリプトのみ
  python3 scripts/gemini_video_analysis.py \\
    --transcript civilink-movie/transcript.md \\
    -o civilink-movie/report.md

  # アップロード済み動画の再利用
  python3 scripts/gemini_video_analysis.py \\
    --transcript civilink-movie/transcript.md \\
    --file-id files/xxxxx \\
    -o civilink-movie/report.md
        """,
    )

    parser.add_argument("--transcript", "-t", required=True,
                        help="トランスクリプト（文字起こし）ファイルのパス")
    parser.add_argument("--video", "-v",
                        help="動画ファイルのパス（省略時はトランスクリプトのみ分析）")
    parser.add_argument("--file-id",
                        help="アップロード済みのGemini File ID (例: files/xxxxx)")
    parser.add_argument("--output", "-o", default="usability_report.md",
                        help="出力レポートのパス (デフォルト: usability_report.md)")
    parser.add_argument("--customer", default="（顧客名未指定）",
                        help="顧客名")
    parser.add_argument("--product-name", default="CiviLink",
                        help="プロダクト名 (デフォルト: CiviLink)")
    parser.add_argument("--model", default="gemini-2.5-flash",
                        help="Geminiモデル (デフォルト: gemini-2.5-flash)")
    parser.add_argument("--env",
                        help=".envファイルのパス")
    parser.add_argument("--tasks",
                        help="タスク定義JSONファイルのパス（テスター・タスク・理想パスを定義）")
    parser.add_argument("--skip-video", action="store_true",
                        help="動画検証をスキップ（トランスクリプトのみで完了）")
    parser.add_argument("--step1-cache",
                        help="Step 1の中間結果JSONを読み込んでStep 2から再開")

    args = parser.parse_args()

    # APIキー読み込み
    api_key = load_api_key(args.env)
    client = genai.Client(api_key=api_key)

    # タスク定義の読み込み
    tasks = load_tasks(args.tasks)

    print(f"プロダクト: {args.product_name}")
    print(f"顧客: {args.customer}")
    print(f"モデル: {args.model}")
    if tasks:
        print(f"タスク定義: {args.tasks}")

    # Step 1: トランスクリプト分析
    if args.step1_cache:
        print(f"\nStep 1キャッシュを読み込み: {args.step1_cache}")
        with open(args.step1_cache) as f:
            cached = json.load(f)
        step1_result = cached.get("step1", cached)
    else:
        step1_result = step1_transcript_analysis(
            client, args.transcript, args.product_name, args.customer, args.model,
            tasks=tasks,
        )

    # Step 2: 動画検証
    step2_verifications = []
    has_video = (args.video or args.file_id) and not args.skip_video
    video_checks = step1_result.get("video_check_segments", [])

    if has_video and video_checks:
        # 動画アップロードまたは既存ファイル使用
        if args.file_id:
            file_id = args.file_id
            try:
                f = client.files.get(name=file_id)
                print(f"\nファイル確認OK: {file_id}")
            except Exception as e:
                print(f"エラー: ファイルID {file_id} が見つかりません: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            file_id = upload_video(client, args.video)

        step2_verifications = step2_video_verification(
            client, file_id, step1_result, args.product_name, args.model
        )
    elif has_video and not video_checks:
        print("\n  Step 1で動画確認が必要な摩擦箇所が検出されませんでした。")
        print("  動画検証をスキップします。")
    else:
        print("\n  動画なし/スキップ。トランスクリプトのみで分析します。")

    # Step 3: 最終レポート生成
    step3_generate_report(
        client, step1_result, step2_verifications,
        args.product_name, args.customer, args.model, args.output
    )

    print(f"\n{'=' * 60}")
    print("完了!")
    print("=" * 60)


if __name__ == "__main__":
    main()

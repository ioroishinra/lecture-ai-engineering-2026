"""第1回の基礎宿題: AIE_MODEL を変え、各質問を各モデルで3回ずつ実行する。

リポジトリのルートで uv run python scripts/compare_models.py を実行する。
生成設定は app.ask と同じ既定値。毎回新しいプロセスで、履歴なしで質問する。
"""

import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone


MODELS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]
QUESTIONS = [
    "LoRAとは何ですか？",
    "AIE2026の講座の宿題にある「3レベル」とは何ですか？",
]
OUTPUT = Path("lectures/01/model_comparison.json")


def main() -> None:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise SystemExit("GEMINI_API_KEY が設定されていません。")
    if OUTPUT.exists():
        raise SystemExit(f"既存の結果を保護するため停止しました: {OUTPUT}")

    result = {
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "models": MODELS,
        "questions": QUESTIONS,
        "repetitions": 3,
        "generation_settings": "app.ask の既定値。temperature 等は指定しない。",
        "context": "各呼び出しは独立。用語集・検索結果・会話履歴は渡さない。",
        "records": [],
    }
    for question in QUESTIONS:
        for repetition in range(1, 4):
            for model in MODELS:
                if result["records"]:
                    time.sleep(10)
                record = {
                    "model": model,
                    "question": question,
                    "repetition": repetition,
                    "started_at_utc": datetime.now(timezone.utc).isoformat(),
                }
                print(f"RUN {len(result['records']) + 1}/12 {model} #{repetition}", flush=True)
                started = time.perf_counter()
                try:
                    completed = subprocess.run(
                        [sys.executable, "-m", "app.ask", question],
                        env={**os.environ, "AIE_MODEL": model},
                        capture_output=True,
                        text=True,
                        timeout=120,
                    )
                    record.update(
                        returncode=completed.returncode,
                        stdout=completed.stdout.replace(key, "[REDACTED]"),
                        stderr=completed.stderr.replace(key, "[REDACTED]"),
                    )
                except subprocess.TimeoutExpired:
                    record.update(returncode=None, stdout="", stderr="120秒でタイムアウト")
                record["elapsed_seconds"] = round(time.perf_counter() - started, 3)
                result["records"].append(record)
                OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                print(f"SAVED returncode={record['returncode']}", flush=True)
                if record["returncode"] != 0:
                    raise SystemExit("実行に失敗しました。結果を保存して停止します。")
    print(f"COMPLETE: {OUTPUT}", flush=True)


if __name__ == "__main__":
    main()

import ast
import json
import re
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_DIR / "backend"))

from app.db import db_cursor  # noqa: E402
from app.ml.labels import KNOWLEDGE_POINTS  # noqa: E402


RAW_QA_PATH = PROJECT_DIR / "data" / "raw" / "高中生物500QA数据.txt"
CLASS_PATH = PROJECT_DIR / "data" / "processed" / "class.txt"
SQL_OUTPUT_PATH = PROJECT_DIR / "data" / "raw" / "high_school_biology_500qa_questions.sql"
SOURCE_NAME = "raw/高中生物500QA数据.txt"
ID_BASE = 500000

LABEL_ALIASES = {
    "网德尔遗传定律": "孟德尔遗传定律",
}

OPTION_LINE_RE = re.compile(r"^([A-D])[.．、]\s*(.+)$")
MALFORMED_ANSWER_RE = re.compile(r"\n\s*[©/]\s*([A-D])。解析[:：]?\s*(.*)$", re.S)
ANSWER_ANALYSIS_RE = re.compile(r"^(.*?)(?:[。.;；]\s*)?解析[:：]\s*(.*)$", re.S)


@dataclass(frozen=True)
class QuestionRow:
    id: int
    stem: str
    options: str | None
    answer: str
    analysis: str | None
    label_id: int
    difficulty: int
    source: str


def normalize_space(value: Any) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\u3000", " ").replace("\xa0", " ")
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def load_class_mapping() -> dict[str, int]:
    labels = [line.strip() for line in CLASS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    return {label: index for index, label in enumerate(labels)}


def normalize_label(label: str) -> str:
    return LABEL_ALIASES.get(label.strip(), label.strip())


def split_question_and_options(text: str) -> tuple[str, str | None]:
    stem_lines: list[str] = []
    option_lines: list[str] = []
    current_option: str | None = None

    for raw_line in text.splitlines():
        line = normalize_space(raw_line)
        if not line:
            continue
        match = OPTION_LINE_RE.match(line)
        if match:
            if current_option:
                option_lines.append(current_option)
            current_option = f"{match.group(1)}. {match.group(2).strip()}"
            continue
        if current_option:
            current_option = f"{current_option} {line}"
        else:
            stem_lines.append(line)

    if current_option:
        option_lines.append(current_option)

    stem = normalize_space(" ".join(stem_lines))
    options = "\n".join(option_lines) if option_lines else None
    return stem, options


def split_answer_and_analysis(raw_answer: str) -> tuple[str, str | None]:
    raw_answer = normalize_space(raw_answer)
    match = ANSWER_ANALYSIS_RE.match(raw_answer)
    if match:
        answer = normalize_space(match.group(1)).strip(" 。.;；，,")
        analysis = normalize_space(match.group(2))
    else:
        answer = raw_answer
        analysis = None

    if not answer:
        answer = "见解析"
    if len(answer) > 255:
        analysis = normalize_space(f"{answer} {analysis or ''}")
        answer = answer[:255]
    return answer, analysis


def extract_answer_block(block_before_labels: str) -> tuple[str, str] | None:
    marker = "\nanswer:"
    if marker in block_before_labels:
        question_text, answer_raw = block_before_labels.split(marker, 1)
        return question_text.strip(), answer_raw.strip()

    match = MALFORMED_ANSWER_RE.search(block_before_labels)
    if match:
        question_text = block_before_labels[: match.start()].strip()
        answer_raw = f"{match.group(1)}。解析：{match.group(2).strip()}"
        return question_text, answer_raw
    return None


def parse_qa_rows() -> tuple[list[QuestionRow], list[dict[str, Any]]]:
    label_to_id = load_class_mapping()
    difficulty_by_label = {item["id"]: int(item["difficulty"]) for item in KNOWLEDGE_POINTS}
    raw_text = RAW_QA_PATH.read_text(encoding="utf-8")
    blocks = [part.strip() for part in re.split(r"\n\s*question:\s*", raw_text) if part.strip()]

    rows: list[QuestionRow] = []
    skipped: list[dict[str, Any]] = []
    for block_index, block in enumerate(blocks, start=1):
        labels_match = re.search(r"\nlabels:\s*(\[.*?\])", block, re.S)
        if not labels_match:
            skipped.append({"block": block_index, "reason": "missing_labels", "preview": block[:120]})
            continue

        answer_parts = extract_answer_block(block[: labels_match.start()].rstrip())
        if not answer_parts:
            skipped.append({"block": block_index, "reason": "missing_answer", "preview": block[:120]})
            continue

        try:
            raw_labels = ast.literal_eval(labels_match.group(1))
        except (SyntaxError, ValueError) as error:
            skipped.append({"block": block_index, "reason": f"invalid_labels:{error}", "preview": labels_match.group(1)})
            continue

        normalized_labels = [normalize_label(label) for label in raw_labels]
        label_name = normalized_labels[0] if normalized_labels else ""
        label_id = label_to_id.get(label_name)
        if label_id is None:
            skipped.append({"block": block_index, "reason": "unknown_label", "labels": raw_labels})
            continue

        question_text, answer_raw = answer_parts
        stem, options = split_question_and_options(question_text)
        answer, analysis = split_answer_and_analysis(answer_raw)
        if not stem:
            skipped.append({"block": block_index, "reason": "empty_stem", "labels": raw_labels})
            continue

        rows.append(
            QuestionRow(
                id=ID_BASE + len(rows) + 1,
                stem=stem,
                options=options,
                answer=answer,
                analysis=analysis,
                label_id=label_id,
                difficulty=max(1, min(5, difficulty_by_label.get(label_id, 3))),
                source=SOURCE_NAME,
            )
        )

    return rows, skipped


def sql_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    return "'" + str(value).replace("\\", "\\\\").replace("'", "''") + "'"


def build_sql(rows: list[QuestionRow], skipped: list[dict[str, Any]]) -> str:
    lines = [
        "-- Generated from data/raw/高中生物500QA数据.txt",
        "-- Deterministic id range: 500001+",
        f"-- Parsed rows: {len(rows)}",
        f"-- Skipped rows: {len(skipped)}",
        "START TRANSACTION;",
        "INSERT INTO questions (id, stem, options, answer, analysis, label_id, difficulty, source)",
        "VALUES",
    ]

    value_lines = []
    for row in rows:
        values = [
            row.id,
            sql_literal(row.stem),
            sql_literal(row.options),
            sql_literal(row.answer),
            sql_literal(row.analysis),
            row.label_id,
            row.difficulty,
            sql_literal(row.source),
        ]
        value_lines.append("    (" + ", ".join(str(value) for value in values) + ")")

    lines.append(",\n".join(value_lines))
    lines.extend(
        [
            "ON DUPLICATE KEY UPDATE",
            "    stem = VALUES(stem),",
            "    options = VALUES(options),",
            "    answer = VALUES(answer),",
            "    analysis = VALUES(analysis),",
            "    label_id = VALUES(label_id),",
            "    difficulty = VALUES(difficulty),",
            "    source = VALUES(source);",
            "COMMIT;",
            "",
        ]
    )
    if skipped:
        lines.append("-- Skipped row report:")
        for item in skipped:
            lines.append("-- " + json.dumps(item, ensure_ascii=False))
    return "\n".join(lines)


def write_sql_file(rows: list[QuestionRow], skipped: list[dict[str, Any]]) -> None:
    SQL_OUTPUT_PATH.write_text(build_sql(rows, skipped), encoding="utf-8")


def insert_rows(rows: list[QuestionRow]) -> None:
    with db_cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO questions (id, stem, options, answer, analysis, label_id, difficulty, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                stem = VALUES(stem),
                options = VALUES(options),
                answer = VALUES(answer),
                analysis = VALUES(analysis),
                label_id = VALUES(label_id),
                difficulty = VALUES(difficulty),
                source = VALUES(source)
            """,
            [
                (
                    row.id,
                    row.stem,
                    row.options,
                    row.answer,
                    row.analysis,
                    row.label_id,
                    row.difficulty,
                    row.source,
                )
                for row in rows
            ],
        )


def main() -> int:
    rows, skipped = parse_qa_rows()
    if not rows:
        print("[ERROR] 没有可导入的 QA 数据", file=sys.stderr)
        return 1

    write_sql_file(rows, skipped)
    insert_rows(rows)

    print(f"SQL 文件已生成: {SQL_OUTPUT_PATH}")
    print(f"questions 表已写入/更新: {len(rows)} 条")
    if skipped:
        print(f"跳过: {len(skipped)} 条，详情见 SQL 文件末尾注释")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

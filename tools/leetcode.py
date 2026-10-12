"""Small, dependency-free helper for a personal LeetCode journal."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
START = "<!-- PROGRESS:START -->"
END = "<!-- PROGRESS:END -->"
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
DIFFICULTIES = ("Easy", "Medium", "Hard")
STATUSES = ("planned", "in-progress", "solved")


def validate(data: dict) -> None:
    if not isinstance(data, dict):
        raise ValueError("problem.json must contain a JSON object")
    if type(data.get("id")) is not int or data["id"] < 1:
        raise ValueError("id must be a positive integer")
    if not isinstance(data.get("slug"), str) or not SLUG.fullmatch(data["slug"]):
        raise ValueError("slug must use lowercase letters, digits, and single hyphens")
    if not isinstance(data.get("title"), str) or not data["title"].strip():
        raise ValueError("title must be nonempty")
    if any(char in data["title"] for char in "\r\n"):
        raise ValueError("title must fit on one line")
    if data.get("difficulty") not in DIFFICULTIES:
        raise ValueError("difficulty must be Easy, Medium, or Hard")
    if data.get("status") not in STATUSES:
        raise ValueError("status must be planned, in-progress, or solved")
    topics = data.get("topics")
    if not isinstance(topics, list) or any(
        not isinstance(topic, str) or not SLUG.fullmatch(topic) for topic in topics
    ):
        raise ValueError("topics must be a list of lowercase hyphenated tags")
    solved_on = data.get("solved_on")
    if data["status"] == "solved":
        if not isinstance(solved_on, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", solved_on):
            raise ValueError("a solved problem needs solved_on in YYYY-MM-DD format")
        date.fromisoformat(solved_on)
    elif solved_on is not None:
        raise ValueError("solved_on must be null until the problem is solved")


def load_problems(root: Path = ROOT) -> list[tuple[Path, dict]]:
    problems = []
    seen = set()
    for folder in sorted((root / "problems").iterdir()):
        if not folder.is_dir() or folder.name.startswith("."):
            continue
        try:
            data = json.loads((folder / "problem.json").read_text(encoding="utf-8"))
            validate(data)
            expected = f"{data['id']:04d}-{data['slug']}"
            if folder.name != expected:
                raise ValueError(f"folder name must be {expected}")
            if data["id"] in seen:
                raise ValueError(f"duplicate problem id: {data['id']}")
            if not (folder / "solution.cpp").is_file() or not (folder / "README.md").is_file():
                raise ValueError("each problem needs solution.cpp and README.md")
            seen.add(data["id"])
            problems.append((folder, data))
        except (ValueError, OSError) as error:
            raise ValueError(f"{folder.name}: {error}") from error
    return sorted(problems, key=lambda item: item[1]["id"])


def markdown(value: str) -> str:
    for char in ("\\", "|", "[", "]", "<", ">", "*", "_", "`"):
        value = value.replace(char, "\\" + char)
    return value


def render_progress(problems: list[tuple[Path, dict]]) -> str:
    solved = [data for _, data in problems if data["status"] == "solved"]
    active = sum(data["status"] == "in-progress" for _, data in problems)
    planned = sum(data["status"] == "planned" for _, data in problems)
    counts = {level: sum(data["difficulty"] == level for data in solved) for level in DIFFICULTIES}
    lines = [
        f"**{len(solved)} solved** · **{active} in progress** · **{planned} planned**",
        "",
        "| Easy solved | Medium solved | Hard solved |",
        "| :---: | :---: | :---: |",
        f"| {counts['Easy']} | {counts['Medium']} | {counts['Hard']} |",
        "",
    ]
    if not problems:
        lines.append("The journal is ready. The first problem will appear here when I start practicing.")
    else:
        lines.extend([
            "| # | Problem | Difficulty | Topics | Status | Solved on |",
            "| --- | --- | --- | --- | --- | --- |",
        ])
        labels = {"planned": "Planned", "in-progress": "In progress", "solved": "Accepted"}
        for folder, data in problems:
            title = markdown(data["title"])
            topics = ", ".join(data["topics"]) or "—"
            lines.append(
                f"| {data['id']} | [{title}](problems/{folder.name}/) | {data['difficulty']} "
                f"| {topics} | {labels[data['status']]} | {data.get('solved_on') or '—'} |"
            )
    return "\n".join(lines)


def refresh(root: Path = ROOT, *, check: bool = False) -> None:
    problems = load_problems(root)
    readme = root / "README.md"
    original = readme.read_text(encoding="utf-8")
    if original.count(START) != 1 or original.count(END) != 1:
        raise ValueError("README.md needs exactly one pair of progress markers")
    before, tail = original.split(START, 1)
    if END not in tail:
        raise ValueError("progress markers are out of order")
    _, after = tail.split(END, 1)
    updated = before + START + "\n" + render_progress(problems) + "\n" + END + after
    if check and original != updated:
        raise ValueError("Progress is outdated. Run: python tools/leetcode.py refresh")
    if not check and original != updated:
        readme.write_text(updated, encoding="utf-8", newline="\n")


def new_problem(args: argparse.Namespace, root: Path = ROOT) -> Path:
    data = {
        "id": args.id,
        "slug": args.slug,
        "title": args.title.strip(),
        "difficulty": args.difficulty,
        "status": "in-progress",
        "topics": sorted(set(args.topics)),
        "solved_on": None,
    }
    validate(data)
    existing = load_problems(root)
    if any(problem["id"] == args.id for _, problem in existing):
        raise ValueError(f"Problem {args.id} already exists")
    folder = root / "problems" / f"{args.id:04d}-{args.slug}"
    template = root / "templates" / "cpp"
    # Read everything before creating the folder; malformed templates leave no partial task.
    sources = {name: (template / name).read_text(encoding="utf-8") for name in ("solution.cpp", "main.cpp")}
    description = (template / "README.md").read_text(encoding="utf-8").format(
        id=args.id,
        title=markdown(data["title"]),
        difficulty=args.difficulty,
        problem_url=f"https://leetcode.com/problems/{args.slug}/",
    )
    folder.mkdir()
    for name, content in sources.items():
        (folder / name).write_text(content, encoding="utf-8", newline="\n")
    (folder / "README.md").write_text(description, encoding="utf-8", newline="\n")
    (folder / "problem.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    refresh(root)
    return folder


def mark_done(problem_id: int, root: Path = ROOT) -> Path:
    for folder, data in load_problems(root):
        if data["id"] == problem_id:
            data["status"] = "solved"
            data["solved_on"] = data.get("solved_on") or date.today().isoformat()
            (folder / "problem.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
            refresh(root)
            return folder
    raise ValueError(f"Problem {problem_id} does not exist")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    new = commands.add_parser("new", help="create a C++ problem folder")
    new.add_argument("id", type=int)
    new.add_argument("slug")
    new.add_argument("--title", required=True)
    new.add_argument("--difficulty", choices=DIFFICULTIES, required=True)
    new.add_argument("--topics", nargs="*", default=[])
    done = commands.add_parser("done", help="mark a problem solved after an Accepted submission")
    done.add_argument("id", type=int)
    commands.add_parser("refresh", help="refresh the progress table")
    commands.add_parser("check", help="validate metadata and check that progress is up to date")
    args = parser.parse_args()
    try:
        if args.command == "new":
            print(f"Created: {new_problem(args)}")
        elif args.command == "done":
            print(f"Marked solved: {mark_done(args.id)}")
        else:
            refresh(check=args.command == "check")
            print("Progress is valid and up to date." if args.command == "check" else "Progress refreshed.")
        return 0
    except (ValueError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

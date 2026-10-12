![LeetCode Lab by dormyyy](.github/assets/banner.svg)

# LeetCode Lab

[![Repository checks](https://github.com/dormyyy/leetcode-lab/actions/workflows/checks.yml/badge.svg)](https://github.com/dormyyy/leetcode-lab/actions/workflows/checks.yml)
![Language: C++17](https://img.shields.io/badge/solutions-C%2B%2B17-00599C?style=flat)
![Focus: problem solving](https://img.shields.io/badge/focus-problem%20solving-ffb454?style=flat)

My personal algorithm practice journal. Each problem gets its own C++ solution, reasoning, complexity analysis, and notes on what I learned.

**Owner:** [@dormyyy](https://github.com/dormyyy) · **Platform:** [LeetCode](https://leetcode.com/) · **Started:** October 2026

## Progress

Only problems marked `solved` after an **Accepted** submission count as solved. This is a self-maintained journal; the repository does not read my LeetCode account.

<!-- PROGRESS:START -->
**0 solved** · **0 in progress** · **0 planned**

| Easy solved | Medium solved | Hard solved |
| :---: | :---: | :---: |
| 0 | 0 | 0 |

The journal is ready. The first problem will appear here when I start practicing.
<!-- PROGRESS:END -->

## Add a problem

From the repository root (Python 3.10+; no packages required):

```powershell
python tools/leetcode.py new 1 two-sum --title "Two Sum" --difficulty Easy --topics array hash-table
```

This creates `problems/0001-two-sum/` with four files:

```text
problems/0001-two-sum/
├── problem.json   # Metadata and progress status
├── README.md      # Approach, correctness, complexity, and lessons
├── solution.cpp   # Code to submit to LeetCode
└── main.cpp       # Local runner; add your own checks
```

Write the solution, add local checks, and explain the approach. After LeetCode returns **Accepted**:

```powershell
python tools/leetcode.py done 1
```

The command records the completion date and refreshes this progress table. You can also create folders by hand: use `0001-two-sum` naming and the same `problem.json` format as in [the guide](docs/START_HERE.ru.md). After manual edits, run:

```powershell
python tools/leetcode.py refresh
```

## Run C++ locally

Open the repository root in **CLion**, reload CMake after adding a problem, and select its `problem_0001-two-sum` run target.

Or use a C++ compiler and CMake from a terminal:

```powershell
cmake -S . -B build
cmake --build build --target problem_0001-two-sum
```

Each folder is built separately. Submit `solution.cpp`; keep local input, custom node definitions, and checks in `main.cpp`.

## Repository map

| Path | Purpose |
| --- | --- |
| [`problems/`](problems/) | One folder per problem; several solution files may live together |
| [`templates/cpp/`](templates/cpp/) | Starter solution, local runner, and explanation template |
| [`tools/leetcode.py`](tools/leetcode.py) | Create tasks and maintain the progress index |
| [`docs/START_HERE.ru.md`](docs/START_HERE.ru.md) | Russian guide to daily use and publishing |
| [GitHub Actions](https://github.com/dormyyy/leetcode-lab/actions) | Metadata, progress-index, helper, and C++ build checks |

CI checks that the repository is consistent and the C++ code builds. Correctness is established through local test cases and LeetCode submissions.

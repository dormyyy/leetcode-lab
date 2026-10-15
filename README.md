![LeetCode Lab by dormyyy](.github/assets/banner.svg)

# LeetCode Lab

[![Repository checks](https://github.com/dormyyy/leetcode-lab/actions/workflows/checks.yml/badge.svg)](https://github.com/dormyyy/leetcode-lab/actions/workflows/checks.yml)
[![Profile sync](https://github.com/dormyyy/leetcode-lab/actions/workflows/sync.yml/badge.svg)](https://github.com/dormyyy/leetcode-lab/actions/workflows/sync.yml)
![Language: C++17](https://img.shields.io/badge/solutions-C%2B%2B17-00599C?style=flat)

My personal algorithm practice journal. Each problem gets its own C++ solution, reasoning, complexity analysis, and notes on what I learned.

**Owner:** [@dormyyy](https://github.com/dormyyy) · **LeetCode:** [dormyyy](https://leetcode.com/u/dormyyy/) · **Started:** October 2026

## Progress

The account counter comes from my public LeetCode profile, including earlier solutions. The repository journal tracks the tasks saved here. Public data does not expose my private submission code.

<!-- PROGRESS:START -->
### LeetCode account · [dormyyy](https://leetcode.com/u/dormyyy/)

**8 solved on LeetCode**

| Easy | Medium | Hard |
| :---: | :---: | :---: |
| 8 | 0 | 0 |

Snapshot updated: 2026-10-12 20:22 (UTC). Includes earlier solutions outside this repository.

### Repository journal

**0 solved** · **1 in progress** · **0 planned**

| Easy solved | Medium solved | Hard solved |
| :---: | :---: | :---: |
| 0 | 0 | 0 |

| # | Problem | Difficulty | Topics | Status | Solved on |
| --- | --- | --- | --- | --- | --- |
| 2 | [Add Two Numbers](problems/0002-add-two-numbers/) | Medium | linked-list, math, recursion | In progress | — |
<!-- PROGRESS:END -->

## One name, one folder

Python 3.10+; no packages, password, or session cookies required:

```powershell
python tools/leetcode.py new add-two-numbers
```

The command downloads the problem number, title, difficulty, tags, original C++ starter signature, and example inputs. Existing solutions are never overwritten.

```text
problems/0002-add-two-numbers/
├── solution.cpp   # Write the algorithm here; paste this file into LeetCode
├── cases.json     # Example inputs; add your own cases and optional expected results
├── main.cpp       # Local entry point, separate from the submitted code
├── types.hpp      # Additional local types, when supplied by the starter
├── problem.json   # Metadata, function signature, and progress
└── README.md      # Approach, correctness, complexity, and lessons
```

## Solve the algorithm, skip stdin

LeetCode calls a method such as `Solution::addTwoNumbers(ListNode*, ListNode*)`. Its array-shaped input represents linked lists; the local runner constructs those nodes automatically.

```powershell
python tools/leetcode.py run add-two-numbers
```

Or open the repository root in **CLion**, reload CMake, and select `problem_0002-add-two-numbers`. CMake regenerates the local calls when `cases.json` changes. Each problem builds independently.

The runner supports scalars, strings, arrays, matrices, linked lists, binary trees, and ordinary design-class operation sequences. Custom judges and unsupported interfaces use an explicit manual-runner fallback. Starter methods throw a clear “implement first” error until I write the solution.

Example inputs print actual outputs. An optional `expected` field adds an output check; check semantics can differ from LeetCode when several answers or output orders are valid. Scalar floating-point checks use a relative/absolute tolerance of `1e-9`. LeetCode's full judge remains the final correctness check.

## Sync the profile

```powershell
python tools/leetcode.py sync
```

GitHub Actions also syncs on relevant pushes and every six hours. It updates the account counter and marks saved, non-starter tasks Accepted when they appear in the public recent Accepted list. That list contains at most 20 entries, not the complete historical archive. For older accepted tasks, use:

```powershell
python tools/leetcode.py done add-two-numbers
```

For browser-to-GitHub code sync, connect **AlgoVault** using [the Opera setup guide](docs/BROWSER_SYNC.ru.md) and [ready-made settings](docs/algovault-settings.json). Accepted submissions go to `browser-sync/`; Actions imports them into the task's `accepted/` archive and updates the journal. It replaces a C++ starter or an unmodified previous import while preserving my own edits and notes. Browser installation and token authorization must be completed separately.

Only meaningful profile/status changes create sync commits. Both author and committer are configured as `dormyyy` with my GitHub noreply email. Failed requests keep the last successful snapshot.

## Repository map

| Path | Purpose |
| --- | --- |
| [`problems/`](problems/) | One folder per task; several approaches can live together |
| [`browser-sync/`](browser-sync/) | Original Accepted code uploaded by AlgoVault |
| [`include/leetcode.hpp`](include/leetcode.hpp) | Local list/tree builders and output checks |
| [`templates/cpp/`](templates/cpp/) | Offline C++ templates |
| [`tools/`](tools/) | Problem import, runner generation, and profile sync |
| [`leetcode.json`](leetcode.json) | Public LeetCode username |
| [`progress/leetcode.json`](progress/leetcode.json) | Last meaningful account snapshot |
| [`docs/START_HERE.ru.md`](docs/START_HERE.ru.md) | Russian guide, cases, and publishing |

CI checks the helper, metadata, progress index, C++ harness, and independent problem builds. It does not submit solutions or claim that unfinished algorithms pass LeetCode.

<!---LeetCode Topics Start-->
# LeetCode Topics
## Linked List
|  |
| ------- |
| [browser-sync/0002-add-two-numbers](https://github.com/dormyyy/leetcode-lab/tree/master/browser-sync/0002-add-two-numbers) |
## Math
|  |
| ------- |
| [browser-sync/0002-add-two-numbers](https://github.com/dormyyy/leetcode-lab/tree/master/browser-sync/0002-add-two-numbers) |
## Recursion
|  |
| ------- |
| [browser-sync/0002-add-two-numbers](https://github.com/dormyyy/leetcode-lab/tree/master/browser-sync/0002-add-two-numbers) |
<!---LeetCode Topics End-->
"""Generate C++ calls from LeetCode examples; no runtime input parser needed."""

import json
import math
import re

IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z_0-9]*")
SCALARS = {"integer": "int", "long": "long long", "long long": "long long", "double": "double", "float": "double", "boolean": "bool", "string": "std::string", "character": "char"}
HEADERS = """#include <algorithm>
#include <array>
#include <cmath>
#include <deque>
#include <functional>
#include <limits>
#include <list>
#include <map>
#include <numeric>
#include <queue>
#include <set>
#include <stack>
#include <stdexcept>
#include <string>
#include <tuple>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

using namespace std;

"""


def cpp_string(value: str) -> str:
    # Fixed-width octal escapes avoid both C++ Unicode restrictions and \x greediness.
    escaped = []
    for byte in value.encode("utf-8"):
        if byte in (34, 92):
            escaped.append("\\" + chr(byte))
        elif 32 <= byte <= 126:
            escaped.append(chr(byte))
        else:
            escaped.append(f"\\{byte:03o}")
    return '"' + "".join(escaped) + '"'


def cpp_type(kind: str) -> str:
    if kind.endswith("[]"):
        return f"std::vector<{cpp_type(kind[:-2])}>"
    if kind in ("ListNode", "TreeNode"):
        return kind + "*"
    if kind not in SCALARS:
        raise ValueError(f"automatic runner does not support type {kind}")
    return SCALARS[kind]


def cpp_value(value, kind: str) -> str:
    if kind.endswith("[]"):
        if not isinstance(value, list):
            raise ValueError(f"{kind} input must be an array")
        return cpp_type(kind) + "{" + ", ".join(cpp_value(item, kind[:-2]) for item in value) + "}"
    if kind in ("ListNode", "TreeNode"):
        if value is None:
            return "nullptr"
        if not isinstance(value, list):
            raise ValueError(f"{kind} input must use LeetCode's array representation")
        if kind == "ListNode":
            values = ", ".join(cpp_value(item, "integer") for item in value)
            return "lc::list({" + values + "})"
        values = ", ".join("std::nullopt" if item is None else cpp_value(item, "integer") for item in value)
        return "lc::tree({" + values + "})"
    if kind == "string" and isinstance(value, str):
        return "std::string(" + cpp_string(value) + ")"
    if kind == "character" and isinstance(value, str) and len(value) == 1 and ord(value) < 128:
        char = cpp_string(value)[1:-1].replace("'", "\\'")
        return "'" + char + "'"
    if kind == "boolean" and type(value) is bool:
        return "true" if value else "false"
    if kind in ("integer", "long", "long long") and type(value) is int:
        limit = 2**31 if kind == "integer" else 2**63
        if not -limit <= value < limit:
            raise ValueError(f"integer is outside {kind} range")
        return str(value) + ("LL" if kind != "integer" else "")
    if kind in ("double", "float") and type(value) in (int, float) and math.isfinite(value):
        return repr(float(value))
    raise ValueError(f"cannot convert {value!r} to {kind}")


def parse_examples(text: str, signature: dict) -> list[dict]:
    lines = [json.loads(line) for line in text.splitlines() if line.strip()]
    size = 2 if signature.get("systemdesign") else len(signature.get("params", []))
    if not size or len(lines) % size:
        raise ValueError("LeetCode examples do not match the parameter count")
    return [{"inputs": lines[index:index + size]} for index in range(0, len(lines), size)]


def solution_source(snippet: str) -> str:
    # Unimplemented methods must compile, but fail explicitly instead of returning garbage.
    parts = re.split(r"(/\*.*?\*/|//[^\n]*)", snippet, flags=re.DOTALL)
    body = '{\n        // TODO: write your algorithm here.\n        throw std::logic_error("Implement the LeetCode method first");\n    }'
    for index in range(0, len(parts), 2):
        parts[index] = re.sub(r"\{\s*\}", lambda _: body, parts[index])
    return HEADERS + "".join(parts) + "\n"


def local_types(snippet: str) -> str:
    # Custom Node definitions are supplied in some starter comments, not in Solution.
    definitions = []
    for comment in re.findall(r"/\*.*?\*/", snippet, flags=re.DOTALL):
        match = re.search(r"(?:class|struct) Node\s*\{.*?\n\s*\};", comment, flags=re.DOTALL)
        if match:
            definitions.append(match.group())
    return "#pragma once\nusing namespace std;\n" + "\n".join(definitions) + "\n"


def identifier(value: str) -> str:
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise ValueError("invalid C++ method or parameter name")
    return value


def normal_case(case: dict, signature: dict, index: int) -> list[str]:
    params = signature["params"]
    inputs = case["inputs"]
    if not isinstance(inputs, list) or len(inputs) != len(params):
        raise ValueError(f"case {index} has the wrong parameter count")
    lines = ["    {", "        Solution solution;"]
    names = []
    for param_index, (param, value) in enumerate(zip(params, inputs)):
        name = f"input_{param_index}"
        names.append(name)
        lines.append(f"        {cpp_type(param['type'])} {name} = {cpp_value(value, param['type'])};")
    call = "solution." + identifier(signature["name"]) + "(" + ", ".join(names) + ")"
    if signature["return"]["type"] == "void":
        output_index = signature.get("output", {}).get("paramindex")
        if type(output_index) is not int or not 0 <= output_index < len(names):
            raise ValueError("void methods need an output parameter in LeetCode metadata")
        lines.append(f"        {call};")
        actual = names[output_index]
    else:
        cpp_type(signature["return"]["type"])
        lines.append(f"        auto actual = {call};")
        actual = "actual"
    lines.append(f'        std::cout << "Case {index}: " << lc::json({actual}) << "\\n";')
    if "expected" in case:
        expected = json.dumps(case["expected"], ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        lines.append(f"        lc::check({actual}, {cpp_string(expected)});")
        lines.append("        ++checked;")
    return lines + ["    }"]


def design_case(case: dict, signature: dict, index: int) -> list[str]:
    operations, arguments = case["inputs"]
    classname = identifier(signature["classname"])
    if not isinstance(operations, list) or not operations or operations[0] != classname or not isinstance(arguments, list) or len(operations) != len(arguments):
        raise ValueError("invalid design-problem operation sequence")
    methods = {method["name"]: method for method in signature["methods"]}
    constructor = signature["constructor"]["params"]
    if len(arguments[0]) != len(constructor):
        raise ValueError("wrong constructor argument count")
    lines = ["    {"]
    names = []
    for index_param, (value, param) in enumerate(zip(arguments[0], constructor)):
        name = f"constructor_arg_{index_param}"
        names.append(name)
        lines.append(f"        {cpp_type(param['type'])} {name} = {cpp_value(value, param['type'])};")
    lines.extend([f"        {classname} solution{{{', '.join(names)}}};", '        std::vector<std::string> outputs{"null"};'])
    for step, (operation, args) in enumerate(zip(operations[1:], arguments[1:]), 1):
        method = methods.get(operation)
        if method is None or len(args) != len(method["params"]):
            raise ValueError("unknown method or wrong argument count in design case")
        names = []
        for param_index, (value, param) in enumerate(zip(args, method["params"])):
            name = f"arg_{step}_{param_index}"
            names.append(name)
            lines.append(f"        {cpp_type(param['type'])} {name} = {cpp_value(value, param['type'])};")
        call = "solution." + identifier(operation) + "(" + ", ".join(names) + ")"
        if method["return"]["type"] == "void":
            lines.extend([f"        {call};", '        outputs.push_back("null");'])
        else:
            cpp_type(method["return"]["type"])
            lines.append(f"        outputs.push_back(lc::json({call}));")
    lines.extend(["        auto actual = lc::join_json(outputs);", f'        std::cout << "Case {index}: " << actual << "\\n";'])
    if "expected" in case:
        expected = json.dumps(case["expected"], ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        lines.append(f"        if (actual != {cpp_string(expected)}) throw std::runtime_error(\"Expected output mismatch\");")
        lines.append("        ++checked;")
    return lines + ["    }"]


def render_driver(signature: dict, cases: list[dict]) -> str:
    if signature.get("manual"):
        raise ValueError("this problem uses a custom judge/interface; add a runner in main.cpp")
    if not isinstance(cases, list) or not cases:
        raise ValueError("cases.json must contain at least one case")
    lines = ["// Generated from problem.json and cases.json. Edit cases.json instead.", "#pragma once", "inline int run_cases() {", "    int checked = 0;"]
    for index, case in enumerate(cases, 1):
        if not isinstance(case, dict):
            raise ValueError("each case must be an object")
        lines.extend((design_case if signature.get("systemdesign") else normal_case)(case, signature, index))
    lines.extend([f'    std::cout << "Ran {len(cases)} case(s); " << checked << " expected-output check(s).\\n";', "    return 0;", "}", ""])
    return "\n".join(lines)


def make_driver(signature: dict, cases: list[dict]) -> tuple[str, str | None]:
    try:
        return render_driver(signature, cases), None
    except (ValueError, KeyError, TypeError) as error:
        reason = str(error)
        return "#pragma once\ninline int run_cases() { throw std::runtime_error(" + cpp_string("Automatic runner unavailable: " + reason) + "); }\n", reason


MAIN = '''#include "../../include/leetcode.hpp"
#include "types.hpp"
#include "solution.cpp"
#include "cases.generated.hpp"

int main() {
    try {
        return run_cases();
    } catch (const std::exception& error) {
        std::cerr << error.what() << "\\n";
        return 1;
    }
}
'''

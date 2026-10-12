#pragma once

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <optional>
#include <queue>
#include <sstream>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <unordered_set>
#include <vector>

struct ListNode {
    int val;
    ListNode* next;
    ListNode() : val(0), next(nullptr) {}
    ListNode(int value) : val(value), next(nullptr) {}
    ListNode(int value, ListNode* tail) : val(value), next(tail) {}
};

struct TreeNode {
    int val;
    TreeNode* left;
    TreeNode* right;
    TreeNode() : val(0), left(nullptr), right(nullptr) {}
    TreeNode(int value) : val(value), left(nullptr), right(nullptr) {}
    TreeNode(int value, TreeNode* lhs, TreeNode* rhs) : val(value), left(lhs), right(rhs) {}
};

namespace lc {
// These builders are for short-lived local test processes. Pointer ownership stays
// with the solution, just as in a judge harness; they do not delete returned nodes.
inline ListNode* list(const std::vector<int>& values) {
    ListNode dummy;
    auto tail = &dummy;
    for (int value : values) {
        tail->next = new ListNode(value);
        tail = tail->next;
    }
    return dummy.next;
}

inline TreeNode* tree(const std::vector<std::optional<int>>& values) {
    if (values.empty() || !values[0]) return nullptr;
    auto root = new TreeNode(*values[0]);
    std::queue<TreeNode*> parents;
    parents.push(root);
    std::size_t index = 1;
    while (!parents.empty() && index < values.size()) {
        auto parent = parents.front();
        parents.pop();
        for (auto slot : {&parent->left, &parent->right}) {
            if (index >= values.size()) break;
            if (values[index]) {
                *slot = new TreeNode(*values[index]);
                parents.push(*slot);
            }
            ++index;
        }
    }
    if (index < values.size()) throw std::runtime_error("Invalid level-order tree input");
    return root;
}

inline std::string json(const std::string& value) {
    std::ostringstream out;
    out << '"';
    for (unsigned char byte : value) {
        if (byte == '"' || byte == '\\') out << '\\' << static_cast<char>(byte);
        else if (byte == '\n') out << "\\n";
        else if (byte == '\r') out << "\\r";
        else if (byte == '\t') out << "\\t";
        else if (byte == '\b') out << "\\b";
        else if (byte == '\f') out << "\\f";
        else if (byte < 32) out << "\\u" << std::hex << std::setw(4) << std::setfill('0') << static_cast<int>(byte) << std::dec;
        else out << static_cast<char>(byte);
    }
    out << '"';
    return out.str();
}
inline std::string json(char value) { return json(std::string(1, value)); }
inline std::string json(bool value) { return value ? "true" : "false"; }
template<class T, std::enable_if_t<std::is_arithmetic_v<T>, int> = 0>
std::string json(T value) {
    std::ostringstream out;
    out << std::setprecision(17) << value;
    return out.str();
}
inline std::string json(ListNode* node) {
    std::ostringstream out;
    std::unordered_set<ListNode*> seen;
    out << '[';
    bool first = true;
    while (node) {
        if (!seen.insert(node).second) throw std::runtime_error("Cycle in list output");
        if (!first) out << ',';
        first = false;
        out << node->val;
        node = node->next;
    }
    out << ']';
    return out.str();
}
inline std::string join_json(const std::vector<std::string>& values) {
    std::string result = "[";
    for (std::size_t index = 0; index < values.size(); ++index) {
        if (index) result += ',';
        result += values[index];
    }
    return result + ']';
}
inline std::string json(TreeNode* root) {
    if (!root) return "[]";
    std::vector<std::string> values;
    std::queue<TreeNode*> nodes;
    std::unordered_set<TreeNode*> seen;
    nodes.push(root);
    while (!nodes.empty()) {
        auto node = nodes.front();
        nodes.pop();
        if (!node) { values.emplace_back("null"); continue; }
        if (!seen.insert(node).second) throw std::runtime_error("Cycle/shared node in tree output");
        values.push_back(std::to_string(node->val));
        nodes.push(node->left);
        nodes.push(node->right);
    }
    while (!values.empty() && values.back() == "null") values.pop_back();
    return join_json(values);
}
template<class T> std::string json(const std::vector<T>& values);
template<class T> std::string json(const std::vector<T>& values) {
    std::vector<std::string> items;
    for (const auto& value : values) items.push_back(json(value));
    return join_json(items);
}
inline std::string json(const std::vector<bool>& values) {
    std::vector<std::string> items;
    for (bool value : values) items.push_back(json(value));
    return join_json(items);
}
template<class T> void check(const T& actual, const std::string& expected) {
    bool equal;
    if constexpr (std::is_floating_point_v<T>) {
        double reference = std::stod(expected);
        equal = std::isfinite(actual) && std::abs(actual - reference) <= 1e-9 * std::max(1.0, std::abs(reference));
    } else {
        equal = json(actual) == expected;
    }
    if (!equal) throw std::runtime_error("Expected " + expected + ", got " + json(actual));
}
} // namespace lc

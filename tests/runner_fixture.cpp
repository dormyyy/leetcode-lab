#include "../include/leetcode.hpp"
#include <cassert>

int main() {
    assert(lc::json(lc::list({2, 4, 3})) == "[2,4,3]");
    assert(lc::json(lc::list({})) == "[]");
    assert(lc::json(lc::tree({1, std::nullopt, 2, 3})) == "[1,null,2,3]");
    assert(lc::json(lc::tree({})) == "[]");
    assert(lc::json(std::vector<std::vector<int>>{{1, 2}, {}}) == "[[1,2],[]]");
    assert(lc::json(std::vector<bool>{true, false}) == "[true,false]");
    assert(lc::json(std::string("a\n\"b")) == "\"a\\n\\\"b\"");
    lc::check(1.0, "1.0000000001");
    bool rejected = false;
    try { lc::check(std::vector<int>{1}, "[2]"); }
    catch (const std::runtime_error&) { rejected = true; }
    assert(rejected);
    auto cyclic = lc::list({1});
    cyclic->next = cyclic;
    rejected = false;
    try { lc::json(cyclic); }
    catch (const std::runtime_error&) { rejected = true; }
    assert(rejected);
    std::cout << "C++ harness checks passed.\n";
}

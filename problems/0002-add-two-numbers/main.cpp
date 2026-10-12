#include "../../include/leetcode.hpp"
#include "types.hpp"
#include "solution.cpp"
#include "cases.generated.hpp"

int main() {
    try {
        return run_cases();
    } catch (const std::exception& error) {
        std::cerr << error.what() << "\n";
        return 1;
    }
}

#include <algorithm>
#include <array>
#include <cmath>
#include <deque>
#include <functional>
#include <iostream>
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

/**
 * Definition for singly-linked list.
 * struct ListNode {
 *     int val;
 *     ListNode *next;
 *     ListNode() : val(0), next(nullptr) {}
 *     ListNode(int x) : val(x), next(nullptr) {}
 *     ListNode(int x, ListNode *next) : val(x), next(next) {}
 * };
 */
class Solution {
public:
    static void print_ll(const ListNode* l, const size_t n) {
        cout<<'[';
        cout<<l->val;
        l = l->next;
        for (size_t i = 0; i < n - 1; i++) {
            cout<<','<<l->val;
            l = l->next;
        }
        cout<<']'<<endl;
    }

    static ListNode* addTwoNumbers(const ListNode* l1, const ListNode* l2) {
        int n = 0;
        int l = 0;
        size_t length = 0;
        ListNode dummy;
        ListNode* tail = &dummy;
        while (l1 != nullptr && l2 != nullptr) {
            const int sum = l1->val + l2->val + l;
            n = sum % 10;
            l = sum / 10;
            tail->next = new ListNode(n);
            tail = tail->next;
            length++;

            l1 = l1->next;
            l2 = l2->next;
        }

        const ListNode* rest = (l1 != nullptr) ? l1 : l2;
        while (rest != nullptr) {
            const int sum = rest->val + l;
            n = sum % 10;
            l = sum / 10;
            tail->next = new ListNode(n);
            tail = tail->next;
            length++;

            rest = rest->next;
        }

        if (l) {
            tail->next = new ListNode(l);
            tail = tail->next;
            length++;
        }
        print_ll(dummy.next, length);
        return dummy.next;
    }
};

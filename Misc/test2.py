#!/usr/bin/env python3
# ------------------------------------------------------------
#  Brute‑force solver for the “COW square‑deletion” problem.
#  It finds the minimum number of operations and one feasible
#  assignment of characters to operations.
# ------------------------------------------------------------

import sys
from functools import lru_cache

# ------------------------------------------------------------------
# helpers
# ------------------------------------------------------------------

def is_square(subseq):
    """return True iff the list of characters `subseq` is a square string."""
    m = len(subseq)
    if m == 0 or (m & 1):
        return False
    half = m // 2
    return subseq[:half] == subseq[half:]


def bits_iter(mask, n):
    """yield positions (0‑based) of the set bits of `mask` (in increasing order)."""
    i = 0
    while mask:
        if mask & 1:
            yield i
        mask >>= 1
        i += 1


# ------------------------------------------------------------------
# core recursive DP (state = frozenset of still‑alive indices)
# ------------------------------------------------------------------

def solve_bruteforce(S):
    """
    Returns
        M                – minimal number of operations,
        ops_list         – list of lists, each inner list contains the
                           original 1‑based indices that are removed
                           in one operation (order of operations is the
                           order of the list).
    """
    n = len(S)
    all_idx = tuple(range(n))               # original positions, 0‑based

    @lru_cache(maxsize=None)
    def dp(state):
        """
        state : frozenset of remaining indices
        returns (min_ops, chosen_subseq) where
            min_ops      – minimal operations to delete everything in `state`,
            chosen_subseq – a tuple of indices (still in `state`) that form
                           a square and are removed in the *first* operation.
                           If state is empty, returns (0, ()).
        """
        if not state:
            return 0, ()

        # convert to a list for indexed access
        cur = list(state)                 # sorted because frozenset iteration is sorted
        L = len(cur)

        best_ops = 10**9
        best_sub = None

        # enumerate every non‑empty subsequence by bitmask (2^L - 1 possibilities)
        #   – L is at most 12‑13 in practice, so this is fine.
        for mask in range(1, 1 << L):
            # quick reject: length must be even
            if (mask.bit_count() & 1):
                continue

            # build the subsequence characters
            seq = [S[cur[i]] for i in range(L) if (mask >> i) & 1]
            if not is_square(seq):
                continue

            # this mask is a legal square subsequence -> remove it
            removed = tuple(cur[i] for i in range(L) if (mask >> i) & 1)
            new_state = frozenset(x for x in state if x not in removed)

            sub_ops, _ = dp(new_state)
            if 1 + sub_ops < best_ops:
                best_ops = 1 + sub_ops
                best_sub = removed

                # optimality test – if we ever reach 1 we can break early
                if best_ops == 1:
                    break

        # The problem statement guarantees that a solution exists when N is even.
        # For odd N the caller will detect impossibility earlier.
        return best_ops, best_sub

    # start from the full set of indices
    full_state = frozenset(all_idx)
    min_ops, first_sub = dp(full_state)

    # rebuild the whole sequence of operations
    ops = []                               # list of lists (1‑based indices)

    def rebuild(state):
        if not state:
            return
        ops_cnt, sub = dp(state)
        # `sub` is the set of indices removed in the first operation for this state
        ops.append([i + 1 for i in sub])    # convert to 1‑based for output
        new_state = frozenset(x for x in state if x not in sub)
        rebuild(new_state)

    rebuild(full_state)

    return min_ops, ops


# ------------------------------------------------------------------
# driver – reads one test case, runs the brute solver and prints the answer
# ------------------------------------------------------------------

def main():
    # input format of the original problem:
    #   T k   (k is ignored for the brute version)
    #   then T test cases: N, S
    temp = input()
    T, k = map(int, temp.split())
    for _ in range(T):
        N = int(input())
        S = input().strip()
        # quick feasibility test (Lemma 1 of the editorial)
        if N & 1:
            print(-1)
            continue

        # run the exponential solver
        M, ops = solve_bruteforce(S)

        # output in the format required by the statement
        print(M)
        # flatten the list of operations into a single array of length 3N
        ans = [0] * (3 * N)
        for op_no, positions in enumerate(ops, start=1):
            for p in positions:
                ans[p - 1] = op_no
        print(' '.join(map(str, ans)))   # space separated

if __name__ == '__main__':
    main()

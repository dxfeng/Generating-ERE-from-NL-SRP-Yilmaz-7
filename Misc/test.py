from heapq import heappush, heappop


def solve():
    n, q = map(int, input().split())
    A = list(map(int, input().split()))
    max_val = max(A)

    # adj[u] will store tuples of (neighbor_value, weight)
    adj = [[] for _ in range(max_val + 1)]

    # 1. Base edges: Incrementing/decrementing value costs 1
    for v in range(1, max_val):
        adj[v].append((v + 1, 1))
        adj[v + 1].append((v, 1))

    # 2. Shortcut edges: Adjacent cells in the array
    for i in range(n - 1):
        u = A[i]
        v = A[i + 1]
        if u != v:
            # The cost to traverse this shortcut is the difference minus 1
            w = abs(u - v) - 1
            adj[u].append((v, w))
            adj[v].append((u, w))

    # Memoization dictionary to cache Dijkstra results
    # memo[start_value] = dist_array
    memo = {}

    def get_shortest_paths(start_node):
        dist = [float('inf')] * (max_val + 1)
        dist[start_node] = 0
        pq = [(0, start_node)]

        while pq:
            d, u = heappop(pq)

            # Optimization: Skip if we've already found a better path
            if d > dist[u]:
                continue

            for v, w in adj[u]:
                if dist[u] + w < dist[v]:
                    dist[v] = dist[u] + w
                    heappush(pq, (dist[v], v))

        return dist

    for _ in range(q):
        # Read each query using standard input
        s, e = map(int, input().split())

        # Convert to 0-based indexing
        s -= 1
        e -= 1

        start_val = A[s]
        end_val = A[e]

        # If we haven't computed the shortest paths from this value yet, do it
        if start_val not in memo:
            memo[start_val] = get_shortest_paths(start_val)

        ans = memo[start_val][end_val]

        # Standard output
        print(ans)


if __name__ == '__main__':
    solve()
```python
# Dynamic Algorithm for calculating the length of the Longest Common Subsequence (LCS) between two lists.
def lcs_length(x, y):
	m = len(x)
	n = len(y)
	c = [[0 for j in range(n + 1)] for i in range(m + 1)]
	for i in range(1,m+1):
		for j in range(1,n+1):
			if x[i - 1] == y[j - 1]:
				c[i][j] = c[i - 1][j - 1] + 1
			elif c[i - 1][j] >= c[i][j - 1]:
				c[i][j] = c[i - 1][j]
			else:
				c[i][j] = c[i][j - 1]
	return [c, c[m][n]]
  
# Dynamic Algorithm for solving the 0/1 knapsack problem
def knapsack(w, b, W):
	B = [[0 for x in range(W + 1)] for x in range(len(b))]
	for i in range(len(b)):
		for j in range(W + 1):
			if w[i] <= j and b[i] + B[i - 1][j-w[i]] > B[i - 1][j]:
				B[i][j] = b[i] + B[i - 1][j-w[i]]
			else:
				B[i][j] = B[i-1][j]
	return [B, B[len(w)-1][W]]

#####
x = lcs_length(['a','b','c','b'], ['b','d','c','a','b'])
print("LCS:")
for i in x[0]:
	print(i)
print("ans:",x[1],"\n")

#####
print("Knapsack:")
x = knapsack([2,3,4,5], [3,4,5,6], 5)
for i in x[0]:
	print(i)
print("ans:",x[1])
```
---
```
LCS:
[0, 0, 0, 0, 0, 0]
[0, 0, 0, 0, 1, 1]
[0, 1, 1, 1, 1, 2]
[0, 1, 1, 2, 2, 2]
[0, 1, 1, 2, 2, 3]
ans: 3

Knapsack:
[0, 0, 3, 3, 3, 3]
[0, 0, 3, 4, 4, 7]
[0, 0, 3, 4, 5, 7]
[0, 0, 3, 4, 5, 7]
ans: 7
```
```python
# Returns the minimum edit distance if each operation has a cost of 1
def minimumEditDistance(string1, string2):
	m = len(string1) + 1
	n = len(string2) + 1
	dp = [[0 for _ in range(n)] for _ in range(m)]
	
	for i in range(m):
		dp[i][0] = i
	
	for j in range(n):
		dp[0][j] = j
	
	for i in range(1, m):
		for j in range(1, n):
			if string1[i - 1] == string2[j - 1]:
				dp[i][j] = dp[i - 1][j - 1]
			else:
				dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
	
	return dp[m-1][n-1]
```

```python
# Returns the minimum edit distance if substitutions have a cost of 2 (Levenshtein's algorithm as per Stanford NLP group on Minimum Edit Distance).
def levenshteinsAlgorithm(string1, string2):
	m = len(string1) + 1
	n = len(string2) + 1
	dp = [[0 for _ in range(n)] for _ in range(m)]
	
	for i in range(m):
		dp[i][0] = i
	
	for j in range(n):
		dp[0][j] = j
	
	for i in range(1, m):
		for j in range(1, n):
			dp[i][j] = min(dp[i - 1][j]+1, dp[i][j - 1]+1, dp[i - 1][j - 1] + (0 if string1[i-1] == string2[j-1] else 2))
	
	return dp[m-1][n-1]
```

```python
def fancyPrint(string1, string2):
	print("Converting", string1, "to", string2, end=":\n")
	print("MED:", minimumEditDistance(string1, string2), "Levenshtein:", levenshteinsAlgorithm(string1, string2))

fancyPrint("spoof", "stool")
fancyPrint("podiatrist", "pediatrician")
fancyPrint("blaming", "conning")
fancyPrint("INTENTION", "EXECUTION")
```

```
Converting spoof to stool:
MED: 2 Levenshtein: 4
Converting podiatrist to pediatrician:
MED: 5 Levenshtein: 8
Converting blaming to conning:
MED: 4 Levenshtein: 8
Converting INTENTION to EXECUTION:
MED: 5 Levenshtein: 8
```
```python
# Dijkstra’s algorithm
  
def Dijkstra(G, w, s):
	print("Dijkstra's algorithm")
	S = {}
	Q = {v: float('inf') for v in G}
	Q[s] = 0
	while Q != {}:
		u = min(Q, key=Q.get)
		S[u] = Q[u]
		print("Removed", u)
		del Q[u]
		for v in G[u]:
			if v in Q:
				if Q[v] > S[u] + w[u][v]:
					Q[v] = S[u] + w[u][v]
	return S
  
#=#=#=#=#=#=#=#
  
# Bellman-Ford algorithm
def BellmanFord(G, w, s):
	print("Bellman-Ford algorithm")
	Q = {v: float('inf') for v in G}
	Q[s] = 0
	for i in range(len(G) - 1):
		for u in G:
			for v in G[u]:
				if Q[v] > Q[u] + w[u][v]:
					Q[v] = Q[u] + w[u][v]
	for u in G:
		for v in G[u]:
			if Q[v] > Q[u] + w[u][v]:
				return False
	return True
  
#=#=#=#=#=#=#=#
graph = {
	'a': {'b': 4, 'c': 6},
	'b': {'c': 8, 'e': 10},
	'c': {'d': 14, 'f': 2},
	'd': {'f': 5},
	'e': {'f': 7, 'g': 2, 'h': 4},
	'f': {'h': 2},
	'g': {'h': 1},
	'h': {}
}

  
G = {}
for node in graph:
	G[node] = list(graph[node].keys())
  
w = {}
for u in G:
	w[u] = {}
	for v in G[u]:
		w[u][v] = graph[u][v]
  
s = 'a'
  
#=#=#=#=#=#=#=#
  
print(Dijkstra(G, w, s))
print()
print(BellmanFord(G, w, s))
```
---
```
Dijkstra's algorithm
Removed a
Removed b
Removed c
Removed f
Removed h
Removed e
Removed g
Removed d
{'a': 0, 'b': 4, 'c': 6, 'f': 8, 'h': 10, 'e': 14, 'g': 16, 'd': 20}

Bellman-Ford algorithm
True
```

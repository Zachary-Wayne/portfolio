```python
# Graph search
class Graph:
    def __init__(self):
        self.color = {}
        self.d = {}
        self.f = {}
        self.pi = {}
        self.adj = {}
        self.time = 0
  
    def addEdge(self,x,y):
        if x not in self.adj.keys():
            self.adj[x] = list()
        self.adj[x].append(y)
  
    def setColorWhite(self):
        for v in self.adj:
            self.color[v] ='white'
            self.d[v] = -1
            self.f[v] = -1
            self.pi[v] = None
            self.time = 0
  
    def dfs_visit(self, G, u):
        self.time += 1
        self.d[u] = self.time
        self.color[u] = 'gray'
        for v in G.adj[u]:
            if self.color[v] == 'white':
                self.pi[v] = u
                self.dfs_visit(G, v) # Recursive Call
        self.color[u] = 'black'
        self.time += 1
        self.f[u] = self.time
  
    def dfs(self,G):
        for v in G.adj:
            if self.color[v] == 'white':
                self.dfs_visit(G, v)
def main():
    g = Graph()
    g.addEdge('a','c')
    g.addEdge('a','e')
    g.addEdge('b','a')
    g.addEdge('b','d')
    g.addEdge('b','e')
    g.addEdge('c','b')
    g.addEdge('d','e')
    g.addEdge('d','f')
    g.addEdge('e','c')
    g.addEdge('f','e')
    g.addEdge('g','d')
    g.addEdge('g','f')
    g.addEdge('g','h')
    g.addEdge('h','e')
    g.setColorWhite()
    g.dfs_visit(g, 'g')
    print(g.d)
    print(g.f)
  
if __name__ == "__main__":
    main()
```
---
```
{'a': 6, 'b': 5, 'c': 4, 'd': 2, 'e': 3, 'f': 11, 'g': 1, 'h': 14}
{'a': 7, 'b': 8, 'c': 9, 'd': 13, 'e': 10, 'f': 12, 'g': 16, 'h': 15}
```

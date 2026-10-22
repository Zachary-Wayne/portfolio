> [!NOTE] #Definition Knapsack Problem 
> Given a set of items, each with a weight and a value, determine which items to include in the collection so that the total weight is less than or equal to a given limit and the total value is as large as possible.
> 
> The most common problem being solved is the **0-1 knapsack problem**, which restricts the number $x_i$ of copies of each kind of item to zero or one. Given a set of $n$ items numbered from 1 up to $n$, each with a weight $w_i$ and a value $v_i$ along with a maximum weight capacity $W$.
 $$\text{maximize } \sum_{i=1}^{n}v_{i}x_{i}$$
 $$\text{subject to }\sum _{i=1}^{n}w_{i}x_{i}\leq W\text{and }x_{i}\in\{0,1\}$$
> Here $x_i$ represents the number of instances of item $i$ to include in the knapsack. Informally, the problem is to maximize the sum of the values of the items in the knapsack so that the sum of the weights is less than or equal to the knapsack's capacity.
## Methods
### Brute Force
Time complexity using a brute force method would result in $O(2^n)$. This method requires testing of all possible combinations.
### Optimum Subproblem 
$\Theta(nW)$
Let $S_k$ be an optimal solution for the set of items $1,2\ldots k$
- The best subset of $S_{k-1}$ that has the total weight $w$.
 $$\begin{align*}OR\end{align*}$$
 - The best subset of $S_{k-1}$ that has a maximum total weight $w-w_k$ plus the value of item $k$.

An implementation of an algorithm can be found in [[Dynamic Programming Activity]].


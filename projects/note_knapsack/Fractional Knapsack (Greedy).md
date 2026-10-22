```python
def fractionalKnapsack(V, weights, W):
	n = len(V)
	max_v = 0
	ratios = []
	percentages = [0]*n
	
	for i in range(n):
		ratios.append((V[i]/weights[i], i)) # Create list of density and index pairs.

	for _, i in sorted(ratios, reverse = True): # Sort by value density, high to low.
		# Put all the high value density items in first if there is space.
		if weights[i] <= W: 
			percentages[i] = 1
			max_v += V[i]
			W -= weights[i]
		# Otherwise add in as much as possible to fill the remaining space and break.
		else:
			f = W / weights[i]
			max_v += V[i] * f
			percentages[i] = f
			break

	return percentages
```

```python
import random
number_of_items = 5

V = [random.randint(5, 50) for _ in range(number_of_items)] # Values
w = [random.randint(1, 20) for _ in range(number_of_items)] # Weights

W = 25.0 # Capacity

ans = fractionalKnapsack(V, w, W)

print("W: ",W)
print("V: ",V)
print("w: ",w)
print("\n")
print("Solution (percentages): ",ans)

total_value = 0
total_weight = 0
for i in range(len(ans)):
	total_value += ans[i] * V[i]
	total_weight += ans[i] * w[i] 
  
print("Total value: ",total_value, ", Total weight:" , total_weight)
```

```
W: 25.0
V: [16, 23, 27, 47, 10]
w: [4, 16, 16, 14, 10]

Solution (percentages): [1, 0, 0.4375, 1, 0]
Total value: 74.8125 , Total weight: 25.0
```
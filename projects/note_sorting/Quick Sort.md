Quick Sort uses a [[Divide and Conquer]] approach to sort arrays:

```python
def quickSort(arr, low, high):                # T(n) = O(n log n)
	if(low < high):                           # O(1)
		p = partition(arr, low, high)         # O(n)
		arr = quickSort(arr, low, p - 1)      # T(n/2)
		arr = quickSort(arr, p + 1, high)     # T(n/2)
	return arr
	
def partition(arr, low, high):   # T(n) = O(n) + O(1)
	pivot = arr[high]            # O(1)
	i = low - 1                  # O(1)
	for j in range(low, high):   # O(n)
		if arr[j] <= pivot:      # O(1)           
			i += 1               # O(1)
			(arr[i], arr[j]) = (arr[j], arr[i]) # O(1)
	i += 1                       # O(1)
	(arr[i], arr[high]) = (arr[high], arr[i]) # O(1)
	return i                     # O(1)

arr = [1,9,4,3,2,5,1,6,7,5,3]
print(quickSort(arr, 0, len(arr)-1))
```

[Additional Quick Sort Information](https://www.geeksforgeeks.org/quick-sort/)
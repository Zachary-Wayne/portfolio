```python
def insertionSort(arr):
	i = 1
	while i < len(arr):
	    j = i
	    while j > 0 and arr[j-1] > arr[j]:
		    temp = arr[j]
		    arr[j] = arr[j-1]
		    arr[j-1] = temp
		    j -= 1
	    i += 1
	return arr

arr = [1,9,4,3,2,5,1,6,7,5,3]
print(insertionSort(arr))
```

[Additional Insertion Sort Information](https://www.geeksforgeeks.org/insertion-sort/)

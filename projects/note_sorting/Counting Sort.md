
```python
# Counting sort for single-digit values (0-9)
def countingSort(array):
    size = len(array)
    output = [0] * size
    count = [0] * 10

    for i in range(0, size):
        count[array[i]] += 1

    for i in range(1, 10):
        count[i] += count[i - 1]

    i = size - 1
    while i >= 0:
        output[count[array[i]] - 1] = array[i]
        count[array[i]] -= 1
        i -= 1

    for i in range(0, size):
        array[i] = output[i]
    return array

arr = [1,9,4,3,2,5,1,6,7,5,3]
print(countingSort(arr))
```
---
```
[1, 1, 2, 3, 3, 4, 5, 5, 6, 7, 9]
```

[Additional Count Sort information](https://www.geeksforgeeks.org/counting-sort/)
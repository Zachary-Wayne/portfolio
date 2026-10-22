### How fast can we sort?
The Lower bound for sorting time complexity is $\Omega(n \log n)$ for comparison sort.

Stirling's Approximation
- $n! = \sqrt{2\pi n}(\frac{n}{e})^n(1+\Theta(\frac{1}{n}))$


| **Algorithm**                                                                                       | **Time Complexity** |                     |                 | **Space Complexity** |
| --------------------------------------------------------------------------------------------------- | ------------------- | ------------------- | --------------- | -------------------- |
|                                                                                                     | **Best**            | **Average**         | **Worst**       | **Worst**            |
| [Selection Sort](https://www.geeksforgeeks.org/selection-sort/)                                     | $\Omega(n^2)$       | $\Theta(n^2)$       | $O(n^2)$        | $O(1)$               |
| [Bubble Sort](https://www.geeksforgeeks.org/bubble-sort/)                                           | $\Omega(n)$         | $\Theta(n^2)$       | $O(n^2)$        | $O(1)$               |
| [[Insertion Sort]]                                                                                  | $\Omega(n)$         | $\Theta(n^2)$       | $O(n^2)$        | $O(1)$               |
| [[Heap]]                                                                                            | $\Omega(n \log(n))$ | $\Theta(n \log(n))$ | $O(n \log(n))$  | $O(1)$               |
| [[Quick Sort]]                                                                                      | $\Omega(n \log(n))$ | $\Theta(n \log(n))$ | $O(n^2)$        | $O(n)$               |
| [Merge Sort](https://www.geeksforgeeks.org/merge-sort/)                                             | $\Omega(n \log(n))$ | $\Theta(n \log(n))$ | $O(n \log(n))$  | $O(n)$               |
| [Bucket Sort](https://www.geeksforgeeks.org/bucket-sort-2/)                                         | $\Omega(n +k)$      | $\Theta(n +k)$      | $O(n^2)$        | $O(n)$               |
| [Radix Sort](https://www.geeksforgeeks.org/radix-sort/)                                             | $\Omega(nk)$        | $\Theta(nk)$        | $O(nk)$         | $O(n + k)$           |
| [[Counting Sort]]                                                                                   | $\Omega(n +k)$      | $\Theta(n +k)$      | $O(n +k)$       | $O(k)$               |
| [Shell Sort](https://www.geeksforgeeks.org/shellsort/)                                              | $\Omega(n \log(n))$ | $\Theta(n \log(n))$ | $O(n^2)$        | $O(1)$               |
| [Tim Sort](https://www.geeksforgeeks.org/timsort/)                                                  | $\Omega(n)$         | $\Theta(n \log(n))$ | $O(n \log (n))$ | $O(n)$               |
| [Tree Sort](https://www.geeksforgeeks.org/tree-sort/)                                               | $\Omega(n \log(n))$ | $\Theta(n \log(n))$ | $O(n^2)$        | $O(n)$               |
| Cube Sort | $\Omega(n)$         | $\Theta(n \log(n))$ | $O(n \log(n))$  | $O(n)$               |
([Source](https://www.geeksforgeeks.org/time-complexities-of-all-sorting-algorithms/))
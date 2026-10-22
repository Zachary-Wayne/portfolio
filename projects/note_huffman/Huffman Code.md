> [!NOTE] #Definition Huffman Code
> Huffman code is a technique for encoding data in which the length of the encoded data is shorter than the original data.
> The Huffman code algorithm is a [[Greedy Algorithm]] that uses the frequency of each character in the input data to create a [[Binary Tree]].
>
> [Huffman Coding](https://en.wikipedia.org/wiki/Huffman_coding)

Suppose we have a file containing 100,000 characters:

| | a | b | c | d | e | f |
|-|-|-|-|-|-|-|
| Frequency (in thousands) | 45 | 13 | 12 | 16 | 9 | 5 |

How can a unique binary string be created from the frequency of each character to minimize the length of the encoded data?

| | a | b | c | d | e | f |
|-|-|-|-|-|-|-|
| Frequency (in thousands) | 45 | 13 | 12 | 16 | 9 | 5 |
| Fixed-length codeword | 000 | 001 | 010 | 011 | 100 | 101 |

By assigning a fixed-length codeword of length 3 to each character, the encoding requires 300,000 bits of storage, this is much more than the 100,000 characters.


| | a | b | c | d | e | f |
|-|-|-|-|-|-|-|
| Frequency (in thousands) | 45 | 13 | 12 | 16 | 9 | 5 |
| Fixed-length codeword | 000 | 001 | 010 | 011 | 100 | 101 |
| Variable-length codeword | 0 | 101 | 100 | 111 | 1101 | 1100 |

With variable-length codeword, the characters that occur more frequently will be encoded with shorter codewords, and the characters that occur less frequently will be encoded with longer codewords.
$$
(45\times1 + 13\times3 + 12\times3 + 16\times3 + 9\times4 + 5\times4) = 244000
$$
Instead of 300,000 bits of storage, using the variable-length codeword encoding requires 244,000 bits of storage.

No codeword in variable-length encoding should be a prefix of another codeword. [Prefix-free Code](https://en.wikipedia.org/wiki/Prefix-free_code). The names of these codewords can be found using the Huffman's algorithm.

To visualize this, every node in the binary tree created as a result of this algorithm will have at most ONE child node that also has child nodes. 

## Huffman's Algorithm Implementation

An implementation of Huffman's algorithm. Re-sorting the nodes every round makes this version $O(n^2\log n)$; keeping them in a min-[[Heap]] instead brings it down to $O(n\log n)$:

```python
class HuffmanNode:
    def __init__(self, char, frequency):
        self.char = char
        self.frequency = frequency
        self.left = None
        self.right = None

class HuffmanTree:
    def __init__(self):
        self.root = None

    def build_tree(self, frequency):
        nodes = [HuffmanNode(char, freq) for char, freq in frequency.items()]

        while len(nodes) > 1:
            nodes = sorted(nodes, key=lambda x: x.frequency)
            left = nodes.pop(0)
            right = nodes.pop(0)
            
            node = HuffmanNode(None, left.frequency + right.frequency)
            node.left = left
            node.right = right
            nodes.append(node)

        self.root = nodes[0]

    def generate_codes(self):
        codes = {} # {Character : Code} Dictionary
        self.recurse(self.root, "", codes)
        return codes

    def recurse(self, node, current_code, codes):
        if node is not None:
            if node.char is not None:
                codes[node.char] = current_code
            self.recurse(node.left, current_code + "0", codes)
            self.recurse(node.right, current_code + "1", codes)

def huffmanCode(string):
    frequency = {}

    for c in string:
        if c in frequency:
            frequency[c] += 1
        else:
            frequency[c] = 1

    huffman_tree = HuffmanTree()
    huffman_tree.build_tree(frequency)
    codes = huffman_tree.generate_codes()

    return codes.items()
```
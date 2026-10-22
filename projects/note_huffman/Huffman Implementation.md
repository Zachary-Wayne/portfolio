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

    def buildTree(self, frequency):
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

    def generateCodes(self):
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
    frequency = {} # List of each character's frequency
    for c in string:
        if c in frequency:
            frequency[c] += 1
        else:
            frequency[c] = 1
    
    huffman_tree = HuffmanTree()
    huffman_tree.buildTree(frequency)
    codes = huffman_tree.generateCodes()

    return codes.items()
```

```python
# Load text from file
#string = open("Some text.txt", "r").read()

string = "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum."

#string = ['a']*49+['b']*13+['c']*12+['d']*16+['e']*9+['f']*5

# Generate codes
codes = huffmanCode(string)

# Print original string from file
print(string)
print("===========")

# Print table
for c, cc in codes:
	print("\""+c+"\"", cc)
print("===========")

# Print original size and encoded size
original_size = len(string) * 8 # Multiplied by 8 because UTF-8 encoding.
encoded_size = 0
for c, cc in codes:
	encoded_size += string.count(c)*len(str(cc))
print("Before encoding: ", original_size)
print("After encoding: ", encoded_size)
print("===========")
```

```
Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum.
===========
"f" 000000
"w" 000001
"y" 00001
"0" 0001000
"M" 00010010
"x" 00010011
"k" 000101
"h" 00011
"e" 001
"a" 0100
"i" 0101
"d" 01100
"." 0110100
"," 0110101
"1" 01101100
"'" 011011010
"5" 011011011
"9" 011011100
"6" 011011101
"A" 011011110
"P" 011011111
"u" 01110
"l" 01111
"m" 10000
"p" 10001
"n" 1001
"s" 1010
"c" 101100
"L" 1011010
"b" 1011011
"g" 101110
"v" 1011110
"I" 1011111
" " 110
"t" 1110
"r" 11110
"o" 11111
===========
Before encoding: 4592
After encoding: 2535
===========
```
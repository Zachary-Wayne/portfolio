Encoding numbers, arithmetic and logic using nothing but functions (Church encodings). A numeral *n* is a function that applies `f` to `x` *n* times.

| Name      | Expression (short)             | Expression (long)                                        |
| --------- | ------------------------------ | -------------------------------------------------------- |
| `0`       | `\f.\x. x`                     | `\f.\x. x`                                               |
| `1`       | `\f.\x. f x`                   | `\f.\x. f x`                                             |
| `2`       | `\f.\x. f (f x)`               | `\f.\x. f (f x)`                                         |
| `Succ`    | `\n.\f.\x. f (n f x)`          | `\n.\f.\x. f (n f x)`                                    |
| `Add`     | `\m.\n. (m Succ n)`            | `\m.\n. (m (\n.\f.\x. f (n f x)) n)`                     |
| `Mult`    | `\m.\n. (m (\x. n Succ x) 0)`  | `\m.\n. (m (\x. n (\n.\f.\x. f (n f x)) x) (\f.\x. x))`  |
| `Power`   | `\m.\n. (n m)`                 | `\m.\n. (n m)`                                           |
| `True`    | `\x.\y. x`                     | `\x.\y. x`                                               |
| `False`   | `\x.\y. y`                     | `\x.\y. y`                                               |
| `AND`     | `\x.\y. (x y False)`           | `\x.\y. (x y (\x.\y. y))`                                |
| `OR`      | `\x.\y. (x True y)`            | `\x.\y. (x (\x.\y. x) y)`                                |
| `NOT`     | `\x. (x False True)`            | `\x. (x (\x.\y. y) (\x.\y. x))`                           |
| `IsZero`  | `\n. n (\x. False) True`       | `\n. n (\x. (\x.\y. y)) (\x.\y. x)`                      |
| `IfElse`  | `\u.\m.\n. ((u m) n)`          | `\u.\m.\n. ((u m) n)`                                    |
| `Pair`    | `\a.\b.\z. z a b`                    | `\a.\b.\z. z a b`                                              |

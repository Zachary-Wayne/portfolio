
## General Stuff
### Regex
This will be true if the string is a valid email. Also note that the output for this first code block is the function.
```clojure
(defn is-email [email]
	(vector?(re-matches #"^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$" email)))
```

```clojure
(is-email "gmail.com")
```

```clojure
(is-email "student@example.com")
```

```clojure
(is-email "wh@t.tf")
```
### List Definition
```clojure
(def some-list [1 4 6 2 4 3])
;(pr some-list)
;(prn some-list)
;(print some-list)
;(println some-list)
```
### Sum of Odd Squares with `for`
```clojure
(apply + (for [x (range 100) :when (odd? x)] (* x x)))
```
### `cond` and `case`
```clojure
(def x 1)
(cond (= x 1) "One" (= 1 2) "Two" :else "Three")
```

```clojure
(case x 1 "One" 2 "Two" "Three")
```
## Dynamic Scoping
```clojure
(def after-tax-price (let [tax 0.14] (fn [price] (+ price (* price tax)))) )
(after-tax-price 10)
```

```clojure
(after-tax-price 500)
```

```clojure
(def ^:dynamic tax 0.09) ; Dynamic top-level symbol
(def dynamic-tax-price (fn [price](+ price (* price tax))))
(dynamic-tax-price 500)
```

This will not change the tax value.
`let` by-design is not able to change dynamic top-level symbols

```clojure
(let [tax 0.15] (dynamic-tax-price 500) ) 
```

```clojure
(binding [tax 0.15] (dynamic-tax-price 500) )
```
---
## Forms
### Comparisons
```clojure
(let [x 100 y 52] (or ( and (> x 0) (> y 0) (< x y))))
```
```clojure
(let [x 100 y 52] (or (> x y 0) (< x y)))
```
```clojure
(if (let [x 100 y 52] (or (> x y 0) (< x y)))
	"Condition is true"
	"Condition is not true")
```
### Conditions and If statements
```clojure
(let [x 50 y 26]
	(cond
		(pos? x) "X is positive" ; Only this will print (regardless of y)
		(pos? y) "Y is positive"
		:else "Neither are positive"))
```
```clojure
(let [x 50 y 26]
	(if (> x y 0) "X and Y are both positive"
		(if (pos? x) "X is positive"
			(if (pos? y) "Y is positive"
				"Neither X or Y are positive"))))
```
### For
```clojure
(for [[course term] [["prog lang" :fall]
                     ["compilers" :winter]
                     ["Machine Learning" :fall]
                     ["database"]]
      :when term]
	(str course " is in "
		(case term
			:fall "the fall semester"
			:winter "the winter semester")))
```
## Loop
```clojure
(loop [name "Zachary" grade 96]
	(str name " got a grade of " grade))
```
## Recursion
```clojure
(defn slow-factorial [n] ; Might lead to a stack overflow and might break.
	(cond (zero? n) 1 ; The deepest recursive call is the starting point.
		:else (* (slow-factorial (dec n)) n)))
		
(slow-factorial 4)
```
### Tail Recursion
```clojure
(defn tail-factorial [n result] ; This will also break
	(cond (zero? n) result 
		:else (tail-factorial (dec n) (* result n))))
```
However, Clojure won't optimise tail recursion automatically, you need to use "recur":
```clojure
(defn tail-factorial [n result]
	(cond (zero? n) result 
				:else (recur (dec n) (* result n))))

(tail-factorial 4 1)
```

Wrapping the accumulator in a `loop` keeps it out of the function's signature, so callers just pass `n`:
```clojure
(defn tail-factorial [n]
	(loop [i n result 1]
		(cond (zero? i) result
			:else (recur (dec i) (* result i)))))

(tail-factorial 4)
```

```clojure
(loop [name "Bob" grade 35]
	(println name "is taking the course...")
	(if (< grade 50)
		(recur name (inc grade))
		(str name " got a grade of " grade)))
```
## Map
```clojure
(def some-map {})
```
### Nested Hashmap
```clojure
(def myclass{
	:title "Calculus"
	:lectures[
		{:day :Monday    :start [11 0] :end [12 20] :room "UA1010"}
		{:day :Wednesday :start [14 0] :end [15 0]  :room "UA1010"}
	]
	:instructor[
		{:first-name "Albert" :last-name "Einstein" :office "UA3030"}
	]
})

(get-in myclass [:lectures 0 :room])
```
## Other Stuff
```clojure
(-> 0 (- 1) (- 1)) ; => -2
```

> [!NOTE] #Definition Master Theorem
> Also known as the Master Method, the Master Theorem provides a way to solve recurrence relations of the form:
> $$\begin{align*} T(n) &= aT(\frac{n}{b}) + f(n) & a&\ge1 & b&>1\\ \end{align*}$$
> Where:
>- $n$ = size of input.
>- $a$ = number of subproblems in the recursion (branches).
>- $\frac{n}{b}$ = size of each subproblem.
>- $f(n)$ = cost of the work done outside the recursive ($T(n)$) call.

The master theorem is used in calculating the time complexity of recurrence relations
([[Divide and Conquer]] Algorithms) in a simple and quick way.
## Cases

$$
\begin{align*}
T(n) &= aT(\frac{n}{b}) + f(n) & a&\ge1 & b&>1\\

\end{align*}
$$
Case 1:
$$
\begin{align*}
f(n)&=O(n^{\log_ba-\epsilon})&\epsilon>0\\
T(n)&=\Theta(n^{\log_ba})
\end{align*}
$$
Case 2:
$$
\begin{align*}
f(n)&=\Theta(n^{\log_ba})\\
T(n)&=\Theta(n^{\log_ba}\log{n})
\end{align*}
$$
Case 3:
$$
\begin{align*}
f(n)&=\Omega(n^{\log_ba+\epsilon});&\epsilon>0\\
T(n)&=\Theta(f(n))
\end{align*}
$$
# Example

$$T(n) = 3T(\frac{n}{2}) + n^2$$
Here,
$$
\begin{align*}
a &= 3\\
\frac{n}{b} &= \frac{n}{2}\\
f(n) &= n^2
\end{align*}
$$

$$
\log_ba = log_23 \approx 1.58 < 2
$$
So, there is a positive constant $\epsilon$ that lets $f(n) < n^{\log_ba+\epsilon}$ hold true.
This can also be written as $f(n)=\Omega(n^{\log_ba+\epsilon})$.
Case 3 implies here. Thus, 
$$
\begin{align*}
T(n) = f(n) &= \Theta(n^2)\\
\therefore 3T(\frac{n}{2}) + n^2 &= \Theta(n^2)
\end{align*}
$$
# Master Theorem Limitations

The master theorem cannot be used if:
- $T(n)$ is not monotone. eg. $T(n) = \sin n$
- $a$ is not a constant. eg. $a = 2n$

[Source](https://www.programiz.com/dsa/master-theorem)
[More Examples](https://www.csd.uwo.ca/~mmorenom/CS433-CS9624/Resources/master.pdf)

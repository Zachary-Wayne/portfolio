import numpy as np


class Utils:
	@staticmethod
	def levenshtein_distance(s1: str, s2: str) -> int:
		if len(s1) < len(s2):
			return Utils.levenshtein_distance(s2, s1)

		if len(s2) == 0:
			return len(s1)

		previous_row = range(0, len(s2) + 1)
		for i, c1 in enumerate(s1):
			current_row = [i + 1]
			for j, c2 in enumerate(s2):
				insertions = previous_row[j + 1] + 1
				deletions = current_row[j] + 1
				substitutions = previous_row[j] + (c1 != c2)
				current_row.append(min(insertions, deletions, substitutions))
			previous_row = current_row

		return previous_row[-1]

	@staticmethod
	def time_task(func):
		def wrapper(*args, **kwargs):
			import time
			start = time.time()
			func(*args, **kwargs)
			end = time.time()
			if '__class__' in dir(args[0]):
				print(f"Time taken for {args[0].__class__.__name__}.{func.__name__}{args[1:]}{kwargs}:"
					  f"\n\t{end - start :.4f} seconds")
			else:
				print(f"Time taken for {func.__name__}{args}{kwargs}:"
					  f"\n\t{end - start :.4f} seconds")
		return wrapper

	@staticmethod
	def lerp(a, b, t):
		a = np.asarray(a)
		b = np.asarray(b)
		t = np.asarray(t)
		return (1 - t) * a + t * b

	@staticmethod
	def map(n, i1, i2, o1, o2):
		if n < i1:
			return o1
		if n > i2:
			return o2
		return o1 + (n - i1) * (o2 - o1) / (i2 - i1)
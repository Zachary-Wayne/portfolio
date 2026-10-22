from projects.profiler_wrapper.profiler_wrapper import profiler_attach

@profiler_attach
def compute_sum(n):
	total = 0
	for i in range(n): total += i
	return total

@profiler_attach(sort_by='tt', condition=lambda x: x > 100)
def process_data(limit):
	return sum(i * i for i in range(limit))

class DataProcessor:
	def __init__(self, size): self._size = size
	def __len__(self): return self._size
	@property
	def limit(self): return self._size * 2
	def _helper(self): return sum(i for i in range(self.limit))


@profiler_attach
def run_pipeline():
	exec("x = 100")

	class DynamicModel:
		pass

	obj = DataProcessor(1000)
	_ = len(obj)
	_ = obj.limit
	return obj._helper()


if __name__ == "__main__":
	compute_sum(1000000)
	process_data(500000)
	run_pipeline()
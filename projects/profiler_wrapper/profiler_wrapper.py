import gc
import os
import re
import builtins
import cProfile
import functools
import inspect
import warnings
from pstats import Stats
from typing import Callable, List, Literal, Tuple

_CLASS_COLOURS: dict[str, int] = {}
_CLASS_COLOUR_PALETTE = [0x4FC3F7, 0x81C784, 0xFFB74D, 0xBA68C8, 0xE57373, 0x4DB6AC, 0xFFD54F, 0x7986CB, 0xF06292, 0xA1887F, 0x64B5F6, 0xAED581]

def blend_colours(c0: int, c1: int, factor: float) -> int:
	factor = max(0.0, min(1.0, factor))
	r0, g0, b0 = (c0 >> 16) & 0xff, (c0 >> 8) & 0xff, c0 & 0xff
	r1, g1, b1 = (c1 >> 16) & 0xff, (c1 >> 8) & 0xff, c1 & 0xff
	rv = int(r0 + (r1 - r0) * factor)
	gv = int(g0 + (g1 - g0) * factor)
	bv = int(b0 + (b1 - b0) * factor)
	return (rv << 16) | (gv << 8) | bv


def colourize(text, fg: int = None, bg: int = None):
	parts = []
	if fg is not None:
		parts.append(f"38;2;{(fg >> 16) & 255};{(fg >> 8) & 255};{fg & 255}")
	if bg is not None:
		parts.append(f"48;2;{(bg >> 16) & 255};{(bg >> 8) & 255};{bg & 255}")

	if not parts:
		return text

	return f"\033[{";".join(parts)}m{text}\033[0m"

def gradient_list(data_list: List[int] | List[float], c0: int, c1: int, decimals: int = -1):
	"""
	A helper function to pretty print a list of numbers and colour them with a gradient.
	"""
	if not data_list:
		return []
	min_val, max_val = min(data_list), max(data_list)
	span = max_val - min_val if max_val != min_val else 1.0
	if decimals == -1:
		return [colourize(val, fg=blend_colours(c0, c1, (val - min_val) / span)) for val in data_list]
	else:
		return [colourize(f"{val:.{decimals}f}", fg=blend_colours(c0, c1, (val - min_val) / span)) for val in data_list]


def find_function_object(filename, lineno, func_name):
	"""
	Locates an active function object in memory by file, line, and name.
	Returns the name if nothing is found. Only use for debugging, no deployment.
	"""

	def _match(f, _fn, _ln):
		try:
			code = f.__code__
			return code.co_firstlineno == _ln and os.path.abspath(code.co_filename) == os.path.abspath(_fn)
		except (AttributeError, TypeError, ValueError):
			return False

	if func_name == "None" or not filename:
		return None
	# noinspection PyTypeChecker
	with warnings.catch_warnings():
		warnings.simplefilter("ignore", FutureWarning)
		warnings.simplefilter("ignore", UserWarning)

		for obj in gc.get_objects():
			if inspect.isfunction(obj) and obj.__name__ == func_name:
				if _match(obj, filename, lineno):
					return obj
			if inspect.isclass(obj):
				for attr_name, attr_value in obj.__dict__.items():
					if isinstance(attr_value, property) and attr_name == func_name:
						# noinspection PyTypeChecker
						if attr_value.fget and _match(attr_value.fget, filename, lineno):
							return attr_value
	return func_name


def method_type_colour(func: Callable | str) -> Tuple[str, str, int, int]:
	"""
	A helper function that takes in a function object and returns coloured text depending on the function type
	"""
	if isinstance(func, str):
		name = func
	else:
		name = func.__name__
	if name == "<lambda>":  # Lambda
		m_type = "lambda"
		fg, bg = 0xFF8800, 0x331100
	elif name.startswith("__") and name.endswith("__"):  # dunderscore
		m_type = "dunder"
		fg, bg = 0xFFFFFF, 0x333333
	elif name.startswith("_"):  # Private
		m_type = "private"
		fg, bg = 0xFF8888, 0x331111
	elif isinstance(func, property):  # Property
		m_type = "property"
		fg, bg = 0x88FFFF, 0x113333
	elif inspect.isgeneratorfunction(func) or name == '<genexpr>':  # Generator
		m_type = "generator"
		fg, bg = 0xFFFF88, 0x333311
	elif inspect.ismethod(func) or inspect.isfunction(func):  # Public
		m_type = "public"
		fg, bg = 0x88FF88, 0x113311
	elif func is builtins.exec or name == 'exec' or name == '<module>':
		m_type = "module"
		fg, bg = 0x8888FF, 0x111133
	elif func is builtins.__build_class__ or name == '__build_class__':
		m_type = "builder"
		fg, bg = 0xff88ff, 0x331133
	else:  # Other
		m_type = "other"
		fg, bg = 0xAAAAAA, 0x111111

	return name, f'[{m_type}]', fg, bg


def get_owner_name(func):
	if func is None: return ""
	qualname = getattr(func, "__qualname__", "")
	if "." in qualname: return qualname.rsplit(".", 1)[0]
	return ""


def get_class_colour(qualname: str) -> int:
	class_name = qualname.rsplit(".", 1)[0] if "." in qualname else qualname
	if class_name not in _CLASS_COLOURS:
		_CLASS_COLOURS[class_name] = _CLASS_COLOUR_PALETTE[len(_CLASS_COLOURS) % len(_CLASS_COLOUR_PALETTE)]
	return _CLASS_COLOURS[class_name]


def split_qualname(qualname: str) -> tuple[str, str]:
	if "." not in qualname: return "", qualname
	class_name, method_name = qualname.rsplit(".", 1)
	return class_name, method_name


def profiler_attach(func: Callable = None, *, sort_by: Literal['cc', 'nc', 'tt', 'ct'] = 'ct', condition: Callable = None):
	"""
	A decorator for to profiling functions. Prints all fancy with colours.
	You can use this decorator as `@profile_lines` for default args.
	Only use for debugging, no deployment.
	"""
	_decimals = 3
	if func is None:
		return functools.partial(profiler_attach, sort_by=sort_by, condition=condition)

	@functools.wraps(func)
	def wrapper(*args, **kwargs):
		if condition is not None and not condition(*args, **kwargs):
			return func(*args, **kwargs)

		with cProfile.Profile() as profiler:
			result = func(*args, **kwargs)

		print(colourize(f"Profiling '{func.__name__}'", 0x191a1c, 0xB7B8BB))
		stats = Stats(profiler)

		sorting_key_dict = {'cc': 0, 'nc': 1, 'tt': 2, 'ct': 3}

		filtered_items = [(key, value) for key, value in stats.stats.items() if 'src' in key[0]]  # type: ignore
		filtered_items.sort(key=lambda item: item[1][sorting_key_dict[sort_by]], reverse=True)
		base_functions, base_function_stats = zip(*filtered_items)
		base_fp, base_ln, base_fn = map(list, zip(*base_functions))  # type: ignore # file path, line number, function name
		base_cc, base_nc, base_tt, base_ct, base_callers = map(list, zip(*base_function_stats))  # type: ignore
		base_func_objs = [find_function_object(fp, ln, fn) for fp, ln, fn in zip(base_fp, base_ln, base_fn)]

		top_callers = []

		for callers, total_calls in zip(base_callers, base_nc):
			if not callers or total_calls == 0:
				top_callers.append((("", 0, "None"), 0.0))
				continue
			caller, (cc, nc, tt, ct) = max(callers.items(), key=lambda item: item[1])
			percentage = nc / total_calls * 100.0
			top_callers.append((caller, percentage))

		caller_keys, caller_percents = zip(*top_callers) if top_callers else ([], [])
		caller_fp, caller_ln, caller_fn = zip(*caller_keys) if caller_keys else ([], [], [])
		caller_fp, caller_ln, caller_fn, caller_percents = map(list, [caller_fp, caller_ln, caller_fn, caller_percents])  # type: ignore
		caller_func_objs = [find_function_object(fp, ln, fn) for fp, ln, fn in zip(caller_fp, caller_ln, caller_fn)]
		caller_q_names = [getattr(f, "__qualname__", fn) for f, fn in zip(caller_func_objs, caller_fn)]

		str_fl = [f'"{os.path.basename(fn)}:{ln}"' for fn, ln in zip(base_fp, base_ln)]
		# noinspection PyTypeChecker
		raw_fn, raw_m, fgs, bgs = zip(*(method_type_colour(f) for f in base_func_objs))

		str_fn = [f'[{a}] {b}' for a, b in zip(raw_m, raw_fn)]
		base_qname = [getattr(f, "__qualname__", fn) for f, fn in zip(base_func_objs, base_fn)]

		headers = [
			"Location",
			"Function",
			"Cumulative Time",
			"Total Time",  # Spent within function, not nested functions.
			"Calls",
			"Frequent Caller"
		]

		# Output formatting and colouring

		str_fl_c = [colourize(fl, 0x548af7) for fl in str_fl]  # Bandaid fix for an IDE visual bug, terminal code links are coloured improperly.
		
		def format_qualname(q_name):
			c_name, m_name = split_qualname(q_name)
			return f"{colourize(c_name, fg=get_class_colour(c_name))}.{m_name}" if c_name else m_name

		str_fn_c = [
			f"{colourize(mode, fg=fg, bg=bg)} {format_qualname(q_name)}"
			for mode, q_name, fg, bg in zip(raw_m, base_qname, fgs, bgs)
			if isinstance(q_name, str)
		]

		str_caller_fn_c = [
			f"{f'[{p:>3.0f}%]':<8} {format_qualname(qn)}{' (recursive)' if qn == oqn else ''}"
			for qn, p, oqn in zip(caller_q_names, caller_percents, base_qname)
			if isinstance(qn, str)
		]

		cols: list[list[int | str]] = [str_fl, str_fn, base_ct, base_tt, base_nc, str_caller_fn_c]
		for col, h in zip(cols, headers):
			col.insert(0, h)

		# str_fn_c = [f'{colourize(mode, fg=fg, bg=bg)} {qualname}' for mode, qualname, fg, bg in zip(raw_m, base_qname, fgs, bgs)]
		str_ct_c = gradient_list(base_ct[1:], 0xB7B8BB, 0xff3333, _decimals)
		str_tt_c = gradient_list(base_tt[1:], 0xB7B8BB, 0xff7747, _decimals)
		str_nc_c = gradient_list(base_nc[1:], 0xB7B8BB, 0xffc04c)

		colored_cols = [str_fl_c, str_fn_c, str_ct_c, str_tt_c, str_nc_c, list(str_caller_fn_c[1:])]
		for cc_col, h in zip(colored_cols, headers):
			cc_col.insert(0, h)

		ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
		widths = [max(len(ansi_escape.sub('', str(s))) for s in col) for col in colored_cols]

		for row in zip(*colored_cols):
			formatted_row = []
			for i, (val, w) in enumerate(zip(row, widths)):
				val_str = str(val)
				pure_len = len(ansi_escape.sub('', val_str))
				padding = w + len(val_str) - pure_len

				if i < 4:
					formatted_row.append(f"{val_str:<{padding}}")
				elif i == 4:
					formatted_row.append(f"{val_str:>{padding}}")
				else:
					formatted_row.append(val_str)

			print("  ".join(formatted_row))

		return result

	return wrapper

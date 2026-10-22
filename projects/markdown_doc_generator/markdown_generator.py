"""
Generates Markdown documentation from Python source code by parsing ASTs, docstrings, and inline comments.

Extracts module structures including classes, methods, functions, type annotations, and formats them into structured Markdown.
"""

import ast
from html import escape
from os import path, walk
from tokenize import generate_tokens, COMMENT, TokenError
from dataclasses import dataclass
from io import StringIO


@dataclass(frozen=True)
class Config:
	@dataclass(frozen=True)
	class Fallbacks:
		default_annotation: str = "..."
		default_value: str = "..."
		type_any: str = "Any"
		no_description: str = "..."
		no_args: str = "None"
		no_usage: str = "*None*"
		empty_desc: str = "..."
		empty_module: str = "*No module variables, functions, or classes found.*\n"

	@dataclass(frozen=True)
	class Headers:
		root_title: str = "# Source File Documentation\n"
		file_prefix: str = "## File: `{filepath}`\n"
		module_desc: str = "### Module Description\n> {doc}\n"
		contents: str = "### Contents\n"
		imports_summary: str = "<summary><b>Imports & Dependencies</b></summary><br>\n"
		todos_summary: str = "<summary><b>TODOs & Tasks</b></summary><br>\n"
		vars_summary: str = "<summary><b>Module Variables & Constants</b></summary><br>\n"
		funcs_summary: str = "<summary><b>Standalone Functions</b></summary><br>\n"
		class_summary: str = "<summary><b>Class:</b> <code>{name}{bases}</code></summary><br>\n"
		class_decorators: str = "<b>Decorators:</b> <code>{decorators}</code><br>"
		class_fields_header: str = "\n<b>Class Attributes / Fields:</b>\n"
		methods_header: str = "\n<b>Methods:</b>\n"

	@dataclass(frozen=True)
	class Tables:
		todos_header: str = "| Line | Description |\n| :--- | :--- |"
		todos_row: str = "| {line} | {todo} |"
		vars_header: str = "| Variable | Type | Default Value |\n| :--- | :--- | :--- |"
		vars_row: str = "| `{name}` | `{type}` | `{val}` |"
		funcs_header: str = "| Function | Description | Arguments | Calls / Instantiates |\n| :--- | :--- | :--- | :--- |"
		funcs_row: str = "| `{name}` | {doc} | `{args}` | {usage} |"
		class_fields_header: str = "| Attribute | Description | Type | Default Value |\n| :--- | :--- | :--- | :--- |"
		class_fields_row: str = "| `{name}` | {doc} | `{type}` | `{val}` |"

	@dataclass(frozen=True)
	class Errors:
		syntax_error: str = "> **Error:** Syntax error parsing file.\n"
		read_error: str = "> **Error:** Failed to read file ({error}).\n"

	@dataclass(frozen=True)
	class Identifiers:
		config_param: str = "config_param"
		field: str = "field"
		default_value: str = "default_value"
		default: str = "default"
		default_factory: str = "default_factory"
		description: str = "description"
		metadata: str = "metadata"
		property_decorator: str = "property"
		async_prefix: str = "async "
		property_prefix: str = "@property "

	@dataclass(frozen=True)
	class FilterLists:
		ignored_builtins: set = (
			"abs", "all", "any", "ascii", "bin", "bool", "breakpoint", "bytearray",
			"bytes", "callable", "chr", "classmethod", "compile", "complex",
			"delattr", "dict", "dir", "divmod", "enumerate", "eval", "exec",
			"filter", "float", "format", "frozenset", "getattr", "globals",
			"hasattr", "hash", "help", "hex", "id", "input", "int", "isinstance",
			"issubclass", "iter", "len", "list", "locals", "map", "max",
			"memoryview", "min", "next", "object", "oct", "open", "ord", "pow",
			"print", "property", "range", "repr", "reversed", "round", "set",
			"setattr", "slice", "sorted", "staticmethod", "str", "sum", "super",
			"tuple", "type", "vars", "zip"
		)
		ignored_methods: set = (
			"append", "extend", "insert", "remove", "pop", "clear", "index",
			"count", "sort", "reverse", "copy", "get", "items", "keys", "values",
			"update", "add", "discard", "union", "strip", "lstrip", "rstrip",
			"split", "rsplit", "join", "replace", "lower", "upper", "startswith",
			"endswith", "find", "rfind", "ljust", "rjust", "center", "format",
			"encode", "decode", "isdigit", "isalpha", "isalnum"
		)
		ignored_refs: set = (
			"True", "False", "None", "Exception", "BaseException", "TypeError",
			"ValueError", "KeyError", "IndexError", "AttributeError", "SyntaxError",
			"RuntimeError", "NameError", "StopIteration", "IOError", "OSError"
		)

	fallbacks: Fallbacks = Fallbacks()
	headers: Headers = Headers()
	tables: Tables = Tables()
	errors: Errors = Errors()
	identifiers: Identifiers = Identifiers()
	filters: FilterLists = FilterLists()


cfg = Config()


def get_annotation_str(node):
	if node is None:
		return cfg.fallbacks.default_annotation
	try:
		return ast.unparse(node)
	except (TypeError, ValueError):
		return cfg.fallbacks.type_any


def sanitize_md(text):
	"""
	Say NO! to code injection.
	"""
	if not text:
		return ""
	text = escape(str(text), quote=False)
	return text.replace("|", "\\|").replace("\n", "<br>")


def extract_docstring_summary(docstring: str | None):
	if not docstring:
		return cfg.fallbacks.no_description

	section_headers = {
		"args:", "arguments:", "parameters:", "params:",
		"returns:", "raises:", "examples:", "example:", "yields:"
	}

	lines = [line.strip() for line in docstring.split("\n")]
	summary_lines = []

	for line in lines:
		if line.lower() in section_headers:
			break
		summary_lines.append(line)

	full_summary = "\n".join(summary_lines).strip()
	return full_summary if full_summary else cfg.fallbacks.no_description


def format_arg(arg, default_node=None):
	arg_str = arg.arg
	if arg.annotation:
		arg_str += f": {get_annotation_str(arg.annotation)}"
	if default_node:
		arg_str += f" = {get_literal_value(default_node)}"
	return arg_str


def get_literal_value(node):
	if node is None:
		return cfg.fallbacks.default_annotation
	try:
		return ast.unparse(node)
	except ValueError:
		return cfg.fallbacks.default_annotation


def extract_field_metadata(node):
	val_str = cfg.fallbacks.default_annotation
	desc = ""

	if not isinstance(node, ast.AnnAssign) or not node.value:
		return val_str, desc

	val_node = node.value

	if isinstance(val_node, ast.Call):
		func_name = get_annotation_str(val_node.func)

		if func_name == cfg.identifiers.config_param:
			if len(val_node.args) >= 1:
				val_str = get_literal_value(val_node.args[0])
			if len(val_node.args) >= 2 and isinstance(val_node.args[1], ast.Constant):
				desc = str(val_node.args[1].value)

			for kw in val_node.keywords:
				if kw.arg == cfg.identifiers.default_value:
					val_str = get_literal_value(kw.value)
				elif kw.arg == cfg.identifiers.description and isinstance(kw.value, ast.Constant):
					desc = str(kw.value.value)

		elif func_name == cfg.identifiers.field:
			for kw in val_node.keywords:
				if kw.arg == cfg.identifiers.default:
					val_str = get_literal_value(kw.value)
				elif kw.arg == cfg.identifiers.default_factory:
					val_str = f"{get_annotation_str(kw.value)}()"
				elif kw.arg == cfg.identifiers.description and isinstance(kw.value, ast.Constant):
					desc = str(kw.value.value)
				elif kw.arg == cfg.identifiers.metadata and isinstance(kw.value, ast.Dict):
					for k, v in zip(kw.value.keys, kw.value.values):
						if isinstance(k, ast.Constant) and k.value == cfg.identifiers.description:
							if isinstance(v, ast.Constant):
								desc = str(v.value)
		else:
			val_str = get_literal_value(val_node)
	else:
		val_str = get_literal_value(val_node)

	return val_str, desc


def extract_internal_references(func_node):
	calls = set()
	refs = set()

	for child in ast.walk(func_node):
		if isinstance(child, ast.Call):
			if isinstance(child.func, ast.Name):
				if child.func.id not in cfg.filters.ignored_builtins:
					calls.add(f"{child.func.id}()")
			elif isinstance(child.func, ast.Attribute):
				if child.func.attr not in cfg.filters.ignored_methods:
					calls.add(f"{get_annotation_str(child.func)}()")
		elif isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
			if child.id[0].isupper() and child.id not in cfg.filters.ignored_refs:
				refs.add(child.id)

	return sorted(list(calls)), sorted(list(refs))


def parse_function_details(func_node):
	name = func_node.name
	args = []

	pos_args = func_node.args.posonlyargs + func_node.args.args
	defaults = [None] * (len(pos_args) - len(func_node.args.defaults)) + list(func_node.args.defaults)

	for arg, default in zip(pos_args, defaults):
		args.append(format_arg(arg, default))

	if func_node.args.vararg:
		var_str = f"*{func_node.args.vararg.arg}"
		if func_node.args.vararg.annotation:
			var_str += f": {get_annotation_str(func_node.args.vararg.annotation)}"
		args.append(var_str)

	for arg, default in zip(func_node.args.kwonlyargs, func_node.args.kw_defaults):
		args.append(format_arg(arg, default))

	if func_node.args.kwarg:
		kw_str = f"**{func_node.args.kwarg.arg}"
		if func_node.args.kwarg.annotation:
			kw_str += f": {get_annotation_str(func_node.args.kwarg.annotation)}"
		args.append(kw_str)

	args_display = ", ".join(args) if args else cfg.fallbacks.no_args
	ret_type = get_annotation_str(func_node.returns) if func_node.returns else cfg.fallbacks.default_annotation

	raw_doc = ast.get_docstring(func_node)
	docstring_clean = sanitize_md(extract_docstring_summary(raw_doc))

	decorators = [get_annotation_str(d) for d in func_node.decorator_list]
	is_property = cfg.identifiers.property_decorator in decorators

	prefix = cfg.identifiers.async_prefix if isinstance(func_node, ast.AsyncFunctionDef) else ""
	if is_property:
		prefix = f"{cfg.identifiers.property_prefix}{prefix}"

	calls, refs = extract_internal_references(func_node)

	return {
		"name": f"{prefix}{name}",
		"args": sanitize_md(args_display),
		"return": sanitize_md(ret_type),
		"doc": docstring_clean,
		"calls": [sanitize_md(c) for c in calls],
		"refs": [sanitize_md(r) for r in refs]
	}


def extract_comments_and_todos(source_code):
	todos = []
	comments = []

	try:
		tokens = generate_tokens(StringIO(source_code).readline)
		for tok_type, tok_string, (srow, _), _, _ in tokens:
			if tok_type == COMMENT:
				clean_comment = tok_string.lstrip("#").strip()
				if "TODO" in tok_string or "FIXME" in tok_string:
					todos.append((srow, clean_comment))
				elif clean_comment:
					comments.append(clean_comment)
	except (TokenError, IndentationError, UnicodeDecodeError):
		pass

	return todos, comments


def parse_imports(tree):
	imports = []
	for node in ast.iter_child_nodes(tree):
		if isinstance(node, ast.Import):
			for alias in node.names:
				imports.append(alias.name)
		elif isinstance(node, ast.ImportFrom):
			module = node.module or ""
			for alias in node.names:
				imports.append(f"{module}.{alias.name}" if module else alias.name)
	return sorted(list(set(imports)))


def generate_markdown_structure(dir_path):
	output = [cfg.headers.root_title]

	root: str
	file: str
	for root, _, files in walk(dir_path):
		for file in sorted(files):
			if file.endswith(".py"):
				# noinspection PyTypeChecker
				filepath = path.join(root, file)
				output.append(cfg.headers.file_prefix.format(filepath=filepath))

				try:
					with open(filepath, "r", encoding="utf-8") as f:
						source = f.read()

					tree = ast.parse(source, filename=file)

					file_docstring = ast.get_docstring(tree)
					if file_docstring:
						clean_file_doc = sanitize_md(extract_docstring_summary(file_docstring))
						output.append(cfg.headers.module_desc.format(doc=clean_file_doc))
					output.append(cfg.headers.contents)

					todos, _ = extract_comments_and_todos(source)
					imports = parse_imports(tree)

					variables = []
					standalone_functions = []
					classes = []

					for node in ast.iter_child_nodes(tree):
						if isinstance(node, ast.Assign):
							for target in node.targets:
								if isinstance(target, ast.Name):
									val = get_literal_value(node.value)
									variables.append((target.id, cfg.fallbacks.default_annotation, val))
						elif isinstance(node, ast.AnnAssign):
							if isinstance(node.target, ast.Name):
								var_type = get_annotation_str(node.annotation)
								val, _ = extract_field_metadata(node)
								variables.append((node.target.id, var_type, val))

						elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
							standalone_functions.append(parse_function_details(node))

						elif isinstance(node, ast.ClassDef):
							raw_class_doc = ast.get_docstring(node)
							class_doc_clean = sanitize_md(extract_docstring_summary(raw_class_doc))

							bases = [get_annotation_str(b) for b in node.bases]
							decorators = [f"@{get_annotation_str(d)}" for d in node.decorator_list]
							methods = []
							class_vars = []

							for item in node.body:
								if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
									methods.append(parse_function_details(item))
								elif isinstance(item, ast.Assign):
									for target in item.targets:
										if isinstance(target, ast.Name):
											val = get_literal_value(item.value)
											class_vars.append((target.id, cfg.fallbacks.default_annotation, val, ""))
								elif isinstance(item, ast.AnnAssign):
									if isinstance(item.target, ast.Name):
										var_type = get_annotation_str(item.annotation)
										val, desc = extract_field_metadata(item)
										class_vars.append((item.target.id, var_type, val, desc))

							classes.append({
								"name": node.name,
								"bases": bases,
								"decorators": decorators,
								"doc": class_doc_clean,
								"methods": methods,
								"class_vars": class_vars
							})

					if imports:
						output.append("<details>")
						output.append(cfg.headers.imports_summary)
						output.append(", ".join([f"`{imp}`" for imp in imports]))
						output.append("\n</details>\n")

					if todos:
						output.append("<details>")
						output.append(cfg.headers.todos_summary)
						output.append(cfg.tables.todos_header)
						for line, todo in todos:
							output.append(cfg.tables.todos_row.format(line=line, todo=sanitize_md(todo)))
						output.append("\n</details>\n")

					if variables:
						output.append("<details>")
						output.append(cfg.headers.vars_summary)
						output.append(cfg.tables.vars_header)
						for var_name, var_type, var_val in variables:
							output.append(cfg.tables.vars_row.format(
								name=sanitize_md(var_name),
								type=sanitize_md(var_type),
								val=sanitize_md(var_val)
							))
						output.append("\n</details>\n")

					if standalone_functions:
						output.append("<details>")
						output.append(cfg.headers.funcs_summary)
						output.append(cfg.tables.funcs_header)
						for func in standalone_functions:
							usage_list = [f"`{c}`" for c in func['calls']] + [f"`{r}`" for r in func['refs']]
							usage_str = ", ".join(usage_list) if usage_list else cfg.fallbacks.no_usage
							output.append(cfg.tables.funcs_row.format(
								name=func['name'],
								args=func['args'],
								usage=usage_str,
								doc=func['doc']
							))
						output.append("\n</details>\n")

					if classes:
						for cls in classes:
							output.append("<details>")
							dec_str = cfg.headers.class_decorators.format(
								decorators=' '.join(cls['decorators'])
							) if cls['decorators'] else ""
							bases_str = f"({', '.join(cls['bases'])})" if cls['bases'] else ""
							output.append(cfg.headers.class_summary.format(
								name=sanitize_md(cls['name']),
								bases=sanitize_md(bases_str)
							))
							if dec_str:
								output.append(f"{dec_str}\n")
							output.append(f"_{cls['doc']}_\n")

							if cls['class_vars']:
								output.append(cfg.headers.class_fields_header)
								output.append(cfg.tables.class_fields_header)
								for cvar_name, cvar_type, cvar_val, cvar_desc in cls['class_vars']:
									desc_str = sanitize_md(cvar_desc) if cvar_desc else cfg.fallbacks.empty_desc
									output.append(cfg.tables.class_fields_row.format(
										name=sanitize_md(cvar_name),
										type=sanitize_md(cvar_type),
										val=sanitize_md(cvar_val),
										doc=desc_str
									))
								output.append("")

							if cls['methods']:
								output.append(cfg.headers.methods_header)
								output.append(cfg.tables.funcs_header)
								for m in cls['methods']:
									usage_list = [f"`{c}`" for c in m['calls']] + [f"`{r}`" for r in m['refs']]
									usage_str = ", ".join(usage_list) if usage_list else cfg.fallbacks.no_usage
									output.append(cfg.tables.funcs_row.format(
										name=m['name'],
										args=m['args'],
										usage=usage_str,
										doc=m['doc']
									))
								output.append("")

							output.append("</details>\n")

					if not variables and not standalone_functions and not classes:
						output.append(cfg.fallbacks.empty_module)

				except SyntaxError:
					output.append(cfg.errors.syntax_error)
				except Exception as e:
					output.append(cfg.errors.read_error.format(error=sanitize_md(str(e))))

	return "\n".join(output)


if __name__ == "__main__":
	markdown_result = generate_markdown_structure(".")
	print(markdown_result)

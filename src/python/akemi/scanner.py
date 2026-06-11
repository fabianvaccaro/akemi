"""Class and interface discovery from source files.

Replaces parse-source.sh with a pure-Python implementation.
Uses Python's ``ast`` module for Python files (most reliable) and
tree-sitter for TypeScript/JavaScript.  Falls back to regex-based
parsing when tree-sitter grammars are not installed.
Java and Scala are scanned with regex only (no extra dependencies).
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class ClassDef:
    """A discovered class or interface definition."""
    name: str
    kind: str  # 'class' or 'interface'
    parents: list[str]
    filepath: str
    line: int
    language: str


# ---------------------------------------------------------------------------
# Skip / enum sets
# ---------------------------------------------------------------------------

FRAMEWORK_SKIP: frozenset[str] = frozenset({
    # Python
    "ABC", "abc.ABC", "Protocol", "typing.Protocol",
    "Generic", "typing.Generic",
    "BaseModel", "BaseSettings", "Base", "DeclarativeBase", "DeclarativeMeta",
    "Exception", "ValueError", "TypeError", "RuntimeError", "KeyError",
    "IOError", "OSError", "NotImplementedError", "object",
    "str", "int", "float", "dict", "list", "tuple", "set", "frozenset",
    # TypeScript / JavaScript
    "Component", "PureComponent", "React.Component", "React.PureComponent",
    "Error", "HTMLElement", "EventTarget", "EventEmitter",
    "Object", "Array", "Map", "Set", "Stream", "Buffer",
    # TS utility types
    "Omit", "Partial", "Pick", "Record", "Required", "Readonly",
    "Extract", "Exclude", "NonNullable", "ReturnType", "InstanceType",
    "Parameters",
    # Java / Scala (Object, Exception and Record are already covered above)
    "RuntimeException", "Throwable", "Serializable", "Comparable", "Enum",
    "AnyRef", "AnyVal", "Product", "App", "Thread",
    "AutoCloseable", "Cloneable",
})

ENUM_PARENTS: frozenset[str] = frozenset({
    "Enum", "enum.Enum", "IntEnum", "StrEnum", "Flag", "IntFlag",
})


# ---------------------------------------------------------------------------
# Tree-sitter setup (lazy, optional)
# ---------------------------------------------------------------------------

_ts_typescript_lang = None
_tsx_lang = None
_js_lang = None
_tree_sitter_available = False

try:
    import tree_sitter_typescript as _ts_typescript_mod  # type: ignore[import-untyped]
    import tree_sitter_javascript as _ts_javascript_mod  # type: ignore[import-untyped]
    from tree_sitter import Language, Parser  # type: ignore[import-untyped]

    _ts_typescript_lang = Language(_ts_typescript_mod.language_typescript())
    _tsx_lang = Language(_ts_typescript_mod.language_tsx())
    _js_lang = Language(_ts_javascript_mod.language())
    _tree_sitter_available = True
except (ImportError, Exception):
    # tree-sitter or grammars not installed; fall back to regex later.
    _tree_sitter_available = False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def scan_file(filepath: str | Path, language: str) -> list[ClassDef]:
    """Dispatch to language-specific scanner.

    Parameters
    ----------
    filepath:
        Absolute or relative path to the source file.
    language:
        One of ``'python'``, ``'typescript'``, ``'javascript'``,
        ``'java'``, ``'scala'``.

    Returns
    -------
    list[ClassDef]
        Discovered class/interface definitions.
    """
    dispatch = {
        "python": scan_python_file,
        "typescript": scan_typescript_file,
        "javascript": scan_javascript_file,
        "java": scan_java_file,
        "scala": scan_scala_file,
    }
    scanner = dispatch.get(language)
    if scanner is None:
        return []
    return scanner(filepath)


# ---------------------------------------------------------------------------
# Python scanner (ast-based)
# ---------------------------------------------------------------------------

def scan_python_file(filepath: str | Path) -> list[ClassDef]:
    """Parse a Python file using the ``ast`` module.

    Extracts top-level class definitions.  Nested classes are skipped.
    Enum subclasses are skipped entirely.
    ABC / Protocol subclasses are tagged as ``kind='interface'``.
    """
    fp = Path(filepath)
    try:
        source = fp.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    try:
        tree = ast.parse(source, filename=str(fp))
    except SyntaxError:
        return []

    results: list[ClassDef] = []

    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, ast.ClassDef):
            continue

        cls_name = node.name
        raw_parents = _extract_python_parents(node)

        # Skip enum classes entirely
        if any(p in ENUM_PARENTS for p in raw_parents):
            continue

        # Determine kind
        kind = "class"
        stripped = {_strip_module_prefix(p) for p in raw_parents}
        if stripped & {"ABC", "Protocol"}:
            kind = "interface"

        # Filter out framework-skip parents.
        # Keep the original dotted name in the parents list (for resolution),
        # but drop those that are in FRAMEWORK_SKIP by either their full name
        # or their stripped suffix.
        filtered_parents: list[str] = []
        for p in raw_parents:
            if p in FRAMEWORK_SKIP:
                continue
            if _strip_module_prefix(p) in FRAMEWORK_SKIP:
                continue
            filtered_parents.append(p)

        results.append(ClassDef(
            name=cls_name,
            kind=kind,
            parents=filtered_parents,
            filepath=str(fp),
            line=node.lineno,
            language="python",
        ))

    return results


def _extract_python_parents(node: ast.ClassDef) -> list[str]:
    """Extract base-class names from an ``ast.ClassDef`` node.

    Handles ``Name``, ``Attribute`` (dotted names), and ``Subscript``
    (e.g. ``Generic[T]`` -- the subscript target is used).
    """
    parents: list[str] = []
    for base in node.bases:
        name = _ast_name(base)
        if name:
            parents.append(name)
    return parents


def _ast_name(node: ast.expr) -> str:
    """Resolve an AST expression to a dotted name string."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _ast_name(node.value)
        if prefix:
            return f"{prefix}.{node.attr}"
        return node.attr
    if isinstance(node, ast.Subscript):
        # Generic[T] -> Generic
        return _ast_name(node.value)
    return ""


def _strip_module_prefix(name: str) -> str:
    """``abc.ABC`` -> ``ABC``, ``typing.Protocol`` -> ``Protocol``."""
    return name.rsplit(".", 1)[-1]


# ---------------------------------------------------------------------------
# TypeScript scanner
# ---------------------------------------------------------------------------

def scan_typescript_file(filepath: str | Path) -> list[ClassDef]:
    """Parse a TypeScript file for class and interface declarations.

    Uses tree-sitter when available; falls back to regex.
    """
    fp = Path(filepath)
    try:
        source = fp.read_bytes()
    except OSError:
        return []

    if _tree_sitter_available:
        # Choose TSX language for .tsx files, standard TS otherwise.
        lang = _tsx_lang if fp.suffix == ".tsx" else _ts_typescript_lang
        return _scan_ts_tree_sitter(source, str(fp), lang, "typescript")

    return _scan_ts_regex(source.decode("utf-8", errors="replace"), str(fp), "typescript")


# ---------------------------------------------------------------------------
# JavaScript scanner
# ---------------------------------------------------------------------------

def scan_javascript_file(filepath: str | Path) -> list[ClassDef]:
    """Parse a JavaScript file for class declarations (no interfaces).

    Uses tree-sitter when available; falls back to regex.
    """
    fp = Path(filepath)
    try:
        source = fp.read_bytes()
    except OSError:
        return []

    if _tree_sitter_available:
        return _scan_js_tree_sitter(source, str(fp))

    return _scan_js_regex(source.decode("utf-8", errors="replace"), str(fp))


# ---------------------------------------------------------------------------
# Tree-sitter implementation (TypeScript)
# ---------------------------------------------------------------------------

def _scan_ts_tree_sitter(
    source: bytes,
    filepath: str,
    ts_lang: object,
    language: str,
) -> list[ClassDef]:
    """Use tree-sitter to extract classes and interfaces from TypeScript."""
    parser = Parser(ts_lang)
    tree = parser.parse(source)
    root = tree.root_node
    results: list[ClassDef] = []

    for node in _ts_iter_top_level(root):
        node_type = node.type

        # ---- Classes (including abstract) ----
        if node_type in ("class_declaration", "abstract_class_declaration"):
            name_node = node.child_by_field_name("name")
            if name_node is None:
                continue
            cls_name = name_node.text.decode("utf-8")

            extends_parents: list[str] = []
            implements_parents: list[str] = []

            heritage = node.child_by_field_name("class_heritage") or _find_child_by_type(node, "class_heritage")
            if heritage is None:
                # Some grammars nest heritage differently; walk direct children.
                for child in node.children:
                    if child.type == "extends_clause":
                        extends_parents.extend(_extract_ts_heritage_names(child))
                    elif child.type == "implements_clause":
                        implements_parents.extend(_extract_ts_heritage_names(child))
            else:
                for child in heritage.children:
                    if child.type == "extends_clause":
                        extends_parents.extend(_extract_ts_heritage_names(child))
                    elif child.type == "implements_clause":
                        implements_parents.extend(_extract_ts_heritage_names(child))

            all_parents = extends_parents + implements_parents
            results.append(ClassDef(
                name=cls_name,
                kind="class",
                parents=all_parents,
                filepath=filepath,
                line=node.start_point[0] + 1,
                language=language,
            ))

        # ---- Interfaces ----
        elif node_type == "interface_declaration":
            name_node = node.child_by_field_name("name")
            if name_node is None:
                continue
            iface_name = name_node.text.decode("utf-8")

            extends_parents = []
            for child in node.children:
                if child.type == "extends_type_clause" or child.type == "extends_clause":
                    extends_parents.extend(_extract_ts_heritage_names(child))

            results.append(ClassDef(
                name=iface_name,
                kind="interface",
                parents=extends_parents,
                filepath=filepath,
                line=node.start_point[0] + 1,
                language=language,
            ))

    return results


def _ts_iter_top_level(root_node: object) -> list:
    """Yield top-level declaration nodes, unwrapping export statements."""
    results = []
    for child in root_node.children:
        ctype = child.type
        if ctype in (
            "class_declaration", "abstract_class_declaration",
            "interface_declaration",
        ):
            results.append(child)
        elif ctype in ("export_statement", "export_default_declaration"):
            # The actual declaration is a child of the export statement.
            for sub in child.children:
                if sub.type in (
                    "class_declaration", "abstract_class_declaration",
                    "interface_declaration",
                ):
                    results.append(sub)
    return results


def _find_child_by_type(node: object, type_name: str) -> object | None:
    """Find the first direct child with the given node type."""
    for child in node.children:
        if child.type == type_name:
            return child
    return None


def _extract_ts_heritage_names(clause_node: object) -> list[str]:
    """Extract class/interface names from an extends or implements clause.

    Strips generic type parameters: ``Component<Props>`` -> ``Component``.
    """
    names: list[str] = []
    for child in clause_node.children:
        # Skip keywords like "extends", "implements", commas
        if child.type in ("extends", "implements", ","):
            continue

        # The heritage value may be a type_identifier, identifier,
        # generic_type (with type_arguments), or member_expression.
        name = _resolve_ts_type_name(child)
        if name:
            names.append(name)
    return names


def _resolve_ts_type_name(node: object) -> str:
    """Resolve a tree-sitter type node to a plain name string.

    Handles: type_identifier, identifier, nested_type_identifier,
    member_expression, generic_type (strips type args).
    """
    ntype = node.type

    if ntype in ("type_identifier", "identifier"):
        return node.text.decode("utf-8")

    if ntype == "nested_type_identifier":
        # e.g., React.Component
        return node.text.decode("utf-8").split("<")[0].strip()

    if ntype == "member_expression":
        return node.text.decode("utf-8").split("<")[0].strip()

    if ntype == "generic_type":
        # First child is the actual type name.
        for child in node.children:
            if child.type in ("type_identifier", "identifier", "nested_type_identifier"):
                return child.text.decode("utf-8")
        # Fallback: strip generics from the whole text.
        return node.text.decode("utf-8").split("<")[0].strip()

    # Fallback for any expression-like node.
    text = node.text.decode("utf-8") if hasattr(node, "text") else ""
    clean = text.split("<")[0].strip()
    # Only return if it looks like an identifier.
    if clean and re.match(r"^[A-Za-z_][\w.]*$", clean):
        return clean

    return ""


# ---------------------------------------------------------------------------
# Tree-sitter implementation (JavaScript)
# ---------------------------------------------------------------------------

def _scan_js_tree_sitter(source: bytes, filepath: str) -> list[ClassDef]:
    """Use tree-sitter to extract class declarations from JavaScript."""
    parser = Parser(_js_lang)
    tree = parser.parse(source)
    root = tree.root_node
    results: list[ClassDef] = []

    for node in _ts_iter_top_level(root):
        if node.type != "class_declaration":
            continue

        name_node = node.child_by_field_name("name")
        if name_node is None:
            continue
        cls_name = name_node.text.decode("utf-8")

        extends_parents: list[str] = []

        # JS heritage: class_heritage or direct extends clause children.
        heritage = _find_child_by_type(node, "class_heritage")
        if heritage is not None:
            for child in heritage.children:
                if child.type == "extends_clause":
                    extends_parents.extend(_extract_ts_heritage_names(child))
        else:
            for child in node.children:
                if child.type == "extends_clause":
                    extends_parents.extend(_extract_ts_heritage_names(child))

        results.append(ClassDef(
            name=cls_name,
            kind="class",
            parents=extends_parents,
            filepath=filepath,
            line=node.start_point[0] + 1,
            language="javascript",
        ))

    return results


# ---------------------------------------------------------------------------
# Regex fallback (TypeScript)
# ---------------------------------------------------------------------------

# Patterns used when tree-sitter is not available.

_RE_TS_CLASS = re.compile(
    r"^(?:export\s+)?(?:default\s+)?(?:abstract\s+)?class\s+"
    r"([A-Za-z_]\w*)"
    r"(?:\s+extends\s+([\w.]+)(?:<[^>]*>)?)?"
    r"(?:\s+implements\s+([^{]+))?"
    ,
    re.MULTILINE,
)

_RE_TS_INTERFACE = re.compile(
    r"^(?:export\s+)?interface\s+"
    r"([A-Za-z_]\w*)"
    r"(?:\s+extends\s+([^{]+))?"
    ,
    re.MULTILINE,
)


def _scan_ts_regex(source: str, filepath: str, language: str) -> list[ClassDef]:
    """Regex fallback for TypeScript class/interface extraction."""
    results: list[ClassDef] = []
    lines = source.split("\n")

    # Build a quick lookup: character offset -> line number.
    line_offsets: list[int] = []
    offset = 0
    for line in lines:
        line_offsets.append(offset)
        offset += len(line) + 1  # +1 for newline

    def _offset_to_line(pos: int) -> int:
        """Convert character offset to 1-based line number."""
        lo, hi = 0, len(line_offsets) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if line_offsets[mid] <= pos:
                lo = mid
            else:
                hi = mid - 1
        return lo + 1

    # Classes
    for m in _RE_TS_CLASS.finditer(source):
        cls_name = m.group(1)
        extends_raw = m.group(2) or ""
        implements_raw = m.group(3) or ""

        parents: list[str] = []
        if extends_raw:
            cleaned = _strip_generics(extends_raw).strip()
            if cleaned:
                parents.append(cleaned)
        if implements_raw:
            for impl in implements_raw.split(","):
                cleaned = _strip_generics(impl).strip()
                if cleaned:
                    parents.append(cleaned)

        results.append(ClassDef(
            name=cls_name,
            kind="class",
            parents=parents,
            filepath=filepath,
            line=_offset_to_line(m.start()),
            language=language,
        ))

    # Interfaces
    for m in _RE_TS_INTERFACE.finditer(source):
        iface_name = m.group(1)
        extends_raw = m.group(2) or ""

        parents = []
        if extends_raw:
            for ext in extends_raw.split(","):
                cleaned = _strip_generics(ext).strip()
                if cleaned:
                    parents.append(cleaned)

        results.append(ClassDef(
            name=iface_name,
            kind="interface",
            parents=parents,
            filepath=filepath,
            line=_offset_to_line(m.start()),
            language=language,
        ))

    return results


# ---------------------------------------------------------------------------
# Regex fallback (JavaScript)
# ---------------------------------------------------------------------------

_RE_JS_CLASS = re.compile(
    r"^(?:export\s+)?(?:default\s+)?class\s+"
    r"([A-Za-z_]\w*)"
    r"(?:\s+extends\s+([\w.]+)(?:<[^>]*>)?)?"
    ,
    re.MULTILINE,
)


def _scan_js_regex(source: str, filepath: str) -> list[ClassDef]:
    """Regex fallback for JavaScript class extraction."""
    results: list[ClassDef] = []
    lines = source.split("\n")

    line_offsets: list[int] = []
    offset = 0
    for line in lines:
        line_offsets.append(offset)
        offset += len(line) + 1

    def _offset_to_line(pos: int) -> int:
        lo, hi = 0, len(line_offsets) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if line_offsets[mid] <= pos:
                lo = mid
            else:
                hi = mid - 1
        return lo + 1

    for m in _RE_JS_CLASS.finditer(source):
        cls_name = m.group(1)
        extends_raw = m.group(2) or ""

        parents: list[str] = []
        if extends_raw:
            cleaned = _strip_generics(extends_raw).strip()
            if cleaned:
                parents.append(cleaned)

        results.append(ClassDef(
            name=cls_name,
            kind="class",
            parents=parents,
            filepath=filepath,
            line=_offset_to_line(m.start()),
            language="javascript",
        ))

    return results


# ---------------------------------------------------------------------------
# Java scanner (regex-based)
# ---------------------------------------------------------------------------

# Matches class/interface/enum/record declarations, with any leading
# modifiers. Anchored at line start (after indentation) so .class
# references and comment lines starting with // or * never match.
_RE_JAVA_DECL = re.compile(
    r"^[ \t]*"
    r"(?:(?:public|protected|private|abstract|final|static|sealed|non-sealed|strictfp)\s+)*"
    r"(class|interface|enum|record)\s+"
    r"([A-Za-z_$][\w$]*)",
    re.MULTILINE,
)


def scan_java_file(filepath: str | Path) -> list[ClassDef]:
    """Parse a Java file for type declarations using regex.

    Handles class, interface, enum and record declarations with
    extends / implements clauses. interface maps to kind 'interface';
    class, enum and record map to kind 'class'.
    """
    fp = Path(filepath)
    try:
        source = fp.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    results: list[ClassDef] = []

    for m in _RE_JAVA_DECL.finditer(source):
        keyword = m.group(1)
        type_name = m.group(2)

        header = _decl_header(source, m.end())
        # Strip generic parameters first: they can contain 'extends'
        # bounds (class Foo<T extends Bar>). Then strip record
        # component lists.
        header = _strip_bracketed(header, "<", ">")
        header = _strip_bracketed(header, "(", ")")
        # Permitted subtypes of a sealed type are not parents.
        header = re.split(r"\bpermits\b", header)[0]

        parents: list[str] = []
        impl_split = re.split(r"\bimplements\b", header, maxsplit=1)
        ext_match = re.search(r"\bextends\b(.*)", impl_split[0], re.DOTALL)
        if ext_match:
            parents.extend(_split_type_list(ext_match.group(1)))
        if len(impl_split) > 1:
            parents.extend(_split_type_list(impl_split[1]))

        results.append(ClassDef(
            name=type_name,
            kind="interface" if keyword == "interface" else "class",
            parents=parents,
            filepath=str(fp),
            line=source.count("\n", 0, m.start()) + 1,
            language="java",
        ))

    return results


# ---------------------------------------------------------------------------
# Scala scanner (regex-based)
# ---------------------------------------------------------------------------

# Matches class, case class, object, case object, trait and enum
# declarations with any leading modifiers.
_RE_SCALA_DECL = re.compile(
    r"^[ \t]*"
    r"(?:(?:abstract|final|sealed|implicit|open|private|protected)\s+)*"
    r"(case\s+class|case\s+object|class|object|trait|enum)\s+"
    r"([A-Za-z_$][\w$]*)",
    re.MULTILINE,
)


def scan_scala_file(filepath: str | Path) -> list[ClassDef]:
    """Parse a Scala file for type declarations using regex.

    Handles class, case class, object, case object, trait and enum.
    trait maps to kind 'interface'; everything else maps to 'class'.
    All names in an 'extends X with Y with Z' chain become parents;
    resolve_refs decides extends vs implements per target kind.
    """
    fp = Path(filepath)
    try:
        source = fp.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    results: list[ClassDef] = []

    for m in _RE_SCALA_DECL.finditer(source):
        keyword = m.group(1)
        type_name = m.group(2)

        header = _scala_decl_header(source, m.end())
        # Strip type parameters ([T]) and constructor parameter lists.
        header = _strip_bracketed(header, "[", "]")
        header = _strip_bracketed(header, "(", ")")
        # Scala 3 'derives' clauses list type classes, not parents.
        header = re.split(r"\bderives\b", header)[0]

        parents: list[str] = []
        ext_match = re.search(r"\bextends\b(.*)", header, re.DOTALL)
        if ext_match:
            for part in re.split(r"\bwith\b", ext_match.group(1)):
                name = part.strip().rstrip(":").strip()
                if re.match(r"^[A-Za-z_$][\w$.]*$", name):
                    parents.append(name)

        results.append(ClassDef(
            name=type_name,
            kind="interface" if keyword == "trait" else "class",
            parents=parents,
            filepath=str(fp),
            line=source.count("\n", 0, m.start()) + 1,
            language="scala",
        ))

    return results


def _decl_header(source: str, pos: int, limit: int = 2000) -> str:
    """Return the declaration header text from *pos* up to the first
    body brace or semicolon."""
    end = min(len(source), pos + limit)
    chunk = source[pos:end]
    for stop in ("{", ";"):
        idx = chunk.find(stop)
        if idx != -1:
            chunk = chunk[:idx]
    return chunk


def _scala_decl_header(source: str, pos: int, limit: int = 2000) -> str:
    """Return a Scala declaration header from *pos*.

    Scala types often have no body, so the header ends at the first
    body brace or at a newline that is outside parens/brackets and is
    not followed by a continuation keyword (extends / with / derives).
    """
    n = min(len(source), pos + limit)
    depth = 0
    i = pos
    chars: list[str] = []
    while i < n:
        ch = source[i]
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        elif ch == "{":
            break
        elif ch == "\n" and depth <= 0:
            j = i + 1
            while j < n and source[j] in " \t":
                j += 1
            if not (
                source.startswith("extends", j)
                or source.startswith("with", j)
                or source.startswith("derives", j)
            ):
                break
        chars.append(ch)
        i += 1
    return "".join(chars)


def _strip_bracketed(text: str, open_ch: str, close_ch: str) -> str:
    """Remove all (possibly nested) bracketed segments from *text*.

    ``_strip_bracketed('Foo<Map<K, V>> extends Bar', '<', '>')``
    returns ``'Foo extends Bar'``.
    """
    out: list[str] = []
    depth = 0
    for ch in text:
        if ch == open_ch:
            depth += 1
        elif ch == close_ch and depth > 0:
            depth -= 1
        elif depth == 0:
            out.append(ch)
    return "".join(out)


def _split_type_list(raw: str) -> list[str]:
    """Split a comma-separated type list, keeping only identifier-like
    names (dotted names allowed). Generics must already be stripped."""
    names: list[str] = []
    for part in raw.split(","):
        name = part.strip()
        if re.match(r"^[A-Za-z_$][\w$.]*$", name):
            names.append(name)
    return names


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _strip_generics(name: str) -> str:
    """Remove generic type parameters: ``Component<Props>`` -> ``Component``."""
    idx = name.find("<")
    if idx != -1:
        return name[:idx].strip()
    return name.strip()


# ---------------------------------------------------------------------------
# Reference resolution (pass 2)
# ---------------------------------------------------------------------------

def resolve_refs(
    defs: list[ClassDef],
) -> list[tuple[ClassDef, list[tuple[str, str]]]]:
    """Two-pass resolution: resolve parent references against discovered defs.

    For each ``ClassDef``, determine for each parent:

    1. Is parent in ``FRAMEWORK_SKIP``? -> skip.
    2. Is parent found in the *defs* list (by name)?
       - Look up the target's ``kind``.
    3. Determine the relationship type:
       - class -> interface parent  =>  ``('implements', target_id)``
       - class -> class parent      =>  ``('extends', target_id)``
       - interface -> interface     =>  ``('extends', target_id)``
    4. If parent not found in defs   ->  skip (external dependency).

    The *target_id* is constructed as ``<prefix>-<kebab-name>``:
    ``cls`` for classes, ``iface`` for interfaces.

    Returns
    -------
    list[tuple[ClassDef, list[tuple[str, str]]]]
        Each element is (definition, list of (rel_type, target_node_id)).
    """
    # Build name -> ClassDef index (first definition wins).
    index: dict[str, ClassDef] = {}
    for d in defs:
        if d.name not in index:
            index[d.name] = d

    results: list[tuple[ClassDef, list[tuple[str, str]]]] = []

    for d in defs:
        refs: list[tuple[str, str]] = []

        for parent in d.parents:
            # Strip generics just in case.
            clean_parent = _strip_generics(parent)

            # Skip framework / stdlib bases.
            if clean_parent in FRAMEWORK_SKIP:
                continue
            if _strip_module_prefix(clean_parent) in FRAMEWORK_SKIP:
                continue

            # Attempt to resolve by the base name (last segment).
            base_parent = _strip_module_prefix(clean_parent)
            target = index.get(clean_parent) or index.get(base_parent)

            if target is None:
                # External dependency - not in project.
                continue

            target_prefix = "iface" if target.kind == "interface" else "cls"
            target_id = f"{target_prefix}-{_to_kebab(target.name)}"

            if d.kind == "class" and target.kind == "interface":
                rel_type = "implements"
            else:
                rel_type = "extends"

            refs.append((rel_type, target_id))

        results.append((d, refs))

    return results


def _strip_module_prefix(name: str) -> str:
    """``abc.ABC`` -> ``ABC``."""
    return name.rsplit(".", 1)[-1]


def _to_kebab(name: str) -> str:
    """Convert a PascalCase / camelCase name to kebab-case.

    Replicates the ``to_kebab`` function from ``node-id-gen.sh``.
    """
    # Insert hyphens before uppercase letters.
    s = re.sub(r"([A-Z])", r"-\1", name)
    # Remove leading hyphen.
    if s.startswith("-"):
        s = s[1:]
    s = s.lower()
    # Replace non-alphanumeric characters with hyphens.
    s = re.sub(r"[^a-z0-9-]", "-", s)
    # Collapse multiple hyphens.
    s = re.sub(r"-{2,}", "-", s)
    # Remove trailing hyphen.
    s = s.rstrip("-")
    return s

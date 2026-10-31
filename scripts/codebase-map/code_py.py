"""The Python layer of the codebase map's Functions tab (installed by the codebase-map skill).

Reads every Python file with Python's own parser (`ast`) and prints, as JSON, the same shape the TypeScript
scanner (code.mjs) produces: every function, method, class and module-level value, with what it takes, what it
gives back, what it calls, the decisions it makes in the order it makes them, what it touches outside the code
(files, network, databases, other programs, the screen) and the env vars it reads. Also the entry points (scripts,
web routes, scheduled jobs, Streamlit pages), which tests use which function, the import graph and the sources.

Standard library only; Python 3.8 or newer. code.mjs runs it with a JSON request on stdin and reads JSON from
stdout; it writes nothing to disk. New framework shapes (a decorator that registers a route, a library call that
reads a file) are taught here, in ENTRY_DECORATORS-style checks and in effect_of().
"""
import ast
import json
import os
import re
import sys

MAX_STEPS = 400
MAX_DOC = 1600
TEST_PATH = re.compile(r"(^|/)(tests?|testing)/|(^|/)test_[^/]+\.py$|_test\.py$|(^|/)conftest\.py$")
SKIP = re.compile(r"(^|/)(\.venv|venv|site-packages|__pycache__|\.tox|\.nox|\.eggs|node_modules|build|dist)/|(^|/)codebase-map/")
HTTP_VERBS = {"get", "post", "put", "patch", "delete", "head", "options"}
import builtins  # noqa: E402

BUILTIN_NAMES = set(dir(builtins))
_INDEX = getattr(ast, "Index", ())


def slice_of(sub):
    """A subscript's index, the same on every Python version."""
    return sub.slice.value if _INDEX and isinstance(sub.slice, _INDEX) else sub.slice
STDLIB = set(getattr(sys, "stdlib_module_names", ())) or {
    "abc", "argparse", "array", "ast", "asyncio", "base64", "bisect", "builtins", "calendar", "collections", "concurrent",
    "contextlib", "copy", "csv", "ctypes", "dataclasses", "datetime", "decimal", "difflib", "email", "enum", "errno",
    "fnmatch", "fractions", "ftplib", "functools", "gc", "getpass", "glob", "gzip", "hashlib", "heapq", "hmac", "html",
    "http", "importlib", "inspect", "io", "ipaddress", "itertools", "json", "logging", "lzma", "math", "mimetypes",
    "multiprocessing", "numbers", "operator", "os", "pathlib", "pickle", "platform", "pprint", "queue", "random", "re",
    "secrets", "select", "shelve", "shlex", "shutil", "signal", "smtplib", "socket", "sqlite3", "ssl", "stat",
    "statistics", "string", "struct", "subprocess", "sys", "tarfile", "tempfile", "textwrap", "threading", "time",
    "timeit", "tomllib", "traceback", "types", "typing", "unicodedata", "unittest", "urllib", "uuid", "warnings",
    "weakref", "xml", "zipfile", "zlib", "zoneinfo",
}

# ------------------------------------------------------------------ what a library call does
# Plain helpers worth no step: pure maths and data handling.
QUIET_PKGS = {"numpy", "pandas", "math", "statistics", "scipy", "typing", "dataclasses", "enum", "itertools",
              "functools", "collections", "operator", "re", "string", "textwrap", "datetime", "copy", "decimal",
              "fractions", "numbers", "random", "uuid", "abc", "types", "inspect", "contextlib", "pprint",
              "bisect", "heapq", "array", "struct", "base64", "binascii", "unicodedata", "difflib", "calendar",
              "zoneinfo", "ast", "keyword", "weakref", "gc", "platform", "getpass", "argparse", "traceback",
              "io", "pathlib", "glob", "fnmatch", "tempfile", "stat", "errno", "signal", "threading",
              "concurrent", "queue", "multiprocessing", "importlib", "builtins", "sys", "os", "time", "json",
              "pickle", "csv", "shlex", "html", "mimetypes", "locale", "codecs", "warnings", "logging", "hashlib",
              "hmac", "secrets", "ipaddress", "zlib", "gzip", "lzma", "bz2", "zipfile", "tarfile", "shutil",
              "asyncio", "socket", "ssl", "select", "selectors", "subprocess", "urllib", "http", "email",
              "smtplib", "sqlite3", "xml", "tomllib", "shelve", "dbm", "unittest", "doctest", "timeit"}
FILE_READ = {
    "pandas": {"read_csv", "read_parquet", "read_json", "read_excel", "read_pickle", "read_feather", "read_table",
               "read_hdf", "read_fwf", "read_orc", "read_stata", "read_sas", "read_spss", "read_xml"},
    "numpy": {"load", "loadtxt", "genfromtxt", "fromfile", "memmap"},
    "json": {"load"}, "pickle": {"load"}, "joblib": {"load"}, "tomllib": {"load"}, "toml": {"load"},
    "geopandas": {"read_file", "read_parquet", "read_feather"},
    "xarray": {"open_dataset", "open_dataarray", "open_mfdataset", "open_zarr", "load_dataset"},
    "h5py": {"File"}, "netCDF4": {"Dataset"}, "fiona": {"open"}, "shelve": {"open"}, "zipfile": {"ZipFile"},
    "tarfile": {"open"}, "gzip": {"open"}, "PIL": {"open"}, "imageio": {"imread"}, "cv2": {"imread"},
    "scipy": {"loadmat"}, "pyarrow": {"read_table", "read_csv", "read_feather"}, "yaml": set(), "glob": set(),
}
FILE_WRITE = {
    "numpy": {"save", "savez", "savez_compressed", "savetxt"},
    "json": {"dump"}, "pickle": {"dump"}, "joblib": {"dump"}, "tomli_w": {"dump"}, "toml": {"dump"},
    "shutil": {"copy", "copy2", "copyfile", "copytree", "move", "rmtree", "make_archive"},
    "os": {"remove", "unlink", "rename", "replace", "rmdir", "removedirs"},
    "matplotlib": {"savefig", "imsave"}, "cv2": {"imwrite"}, "scipy": {"savemat"}, "imageio": {"imwrite"},
    "pyarrow": {"write_table"},
}
METHOD_READ = {"read_text", "read_bytes"}
METHOD_WRITE = {"to_csv", "to_parquet", "to_json", "to_excel", "to_pickle", "to_feather", "to_file", "to_netcdf",
                "to_zarr", "to_hdf", "to_orc", "write_text", "write_bytes", "savefig", "tofile", "to_raster"}
NETWORK_PKGS = {"requests", "httpx", "aiohttp", "urllib3", "openmeteo_requests", "cdsapi", "earthaccess",
                "pystac_client", "sentinelhub", "openeo", "paramiko", "ftplib", "websocket", "websockets",
                "stripe", "razorpay", "openai", "anthropic", "slack_sdk", "twilio", "tweepy", "gspread"}
EMAIL_PKGS = {"smtplib", "sendgrid", "resend", "yagmail", "postmarker", "mailjet_rest"}
SCREEN_PKGS = {"streamlit"}


def effect_of(pkg, fn, qual, call, imports):
    """What a library call does, in one word, or None for helpers not worth a step."""
    if pkg == "builtins":
        if fn == "open":
            return file_mode(call, 1)
        if fn in ("exit", "quit"):
            return "exit"
        if fn == "input":
            return "request"
        return None
    if pkg in SCREEN_PKGS:
        if re.search(r"\.(session_state|secrets|query_params|context)\b", qual):
            return None
        if fn in ("stop", "rerun", "experimental_rerun"):
            return "exit"
        if fn in ("cache_data", "cache_resource", "cache", "experimental_memo") or fn == "clear":
            return "cache" if fn == "clear" else None
        return "screen"
    if pkg == "os" and (qual.startswith("os.environ") or fn in ("getenv", "environ")):
        return None
    if pkg in FILE_READ and fn in FILE_READ[pkg]:
        return "file-read"
    if pkg in FILE_WRITE and fn in FILE_WRITE[pkg]:
        return "file-write"
    if pkg == "rasterio" and fn == "open":
        return file_mode(call, 1)
    if pkg == "matplotlib" and fn == "savefig":
        return "file-write"
    if pkg in ("subprocess",) and fn in ("run", "Popen", "call", "check_call", "check_output"):
        return "process"
    if pkg == "os" and fn in ("system", "popen", "startfile", "execv", "execvp", "spawnv"):
        return "process"
    if pkg == "asyncio" and fn in ("create_subprocess_exec", "create_subprocess_shell"):
        return "process"
    if (pkg == "sys" and fn == "exit") or (pkg == "os" and fn == "_exit"):
        return "exit"
    if pkg in ("time", "asyncio") and fn == "sleep":
        return "wait"
    if pkg == "logging" and fn in ("warning", "warn", "error", "exception", "critical"):
        return "log"
    if pkg == "warnings" and fn == "warn":
        return "log"
    if pkg in ("hashlib", "hmac", "secrets", "bcrypt", "jwt", "cryptography", "nacl"):
        return "crypto"
    if pkg in ("urllib",) and fn in ("urlopen", "urlretrieve"):
        return "network"
    if pkg == "http" and fn in ("HTTPConnection", "HTTPSConnection"):
        return "network"
    if pkg in NETWORK_PKGS:
        if fn in ("Session", "Client", "AsyncClient", "ClientSession"):
            return "setup"
        return "network"
    if pkg in EMAIL_PKGS:
        return "setup" if fn in ("SMTP", "SMTP_SSL") else "email"
    if pkg == "ee":
        if fn in ("Initialize", "Authenticate", "ServiceAccountCredentials"):
            return "setup"
        if fn in ("computePixels", "getDownloadURL", "getThumbURL", "getInfo", "getPixels", "listAssets"):
            return "network"
        return None
    if pkg == "boto3":
        return "setup"
    if pkg == "google" and ".storage" in qual:
        return "storage"
    if pkg in ("sqlite3", "psycopg", "psycopg2", "pymysql", "duckdb", "sqlalchemy", "mysql", "pymongo", "redis"):
        if fn in ("connect", "create_engine", "MongoClient", "Redis", "StrictRedis", "sessionmaker"):
            return "setup"
        return None
    if pkg == "pandas" and fn == "read_sql":
        return "db-read"
    if pkg == "dotenv" or (pkg == "logging" and fn in ("basicConfig", "getLogger")):
        return "setup"
    if pkg == "modal":
        if fn in ("App", "Stub", "Image", "Volume", "Secret", "Cron", "Period", "from_name", "debian_slim",
                  "pip_install", "apt_install", "env", "is_local", "add_local_dir", "add_local_file"):
            return "setup" if fn in ("App", "Stub", "from_name") else None
        return "lib"
    if pkg == "flask":
        if fn == "redirect":
            return "redirect"
        if fn == "abort":
            return "notfound"
        if fn in ("render_template", "jsonify", "make_response", "send_file"):
            return "response"
        return None
    if pkg in ("fastapi", "starlette"):
        if fn in ("JSONResponse", "HTMLResponse", "RedirectResponse", "Response", "StreamingResponse", "FileResponse"):
            return "redirect" if fn == "RedirectResponse" else "response"
        if fn == "HTTPException":
            return None
        return None
    if pkg in ("pydantic", "jsonschema") and fn in ("model_validate", "parse_obj", "validate", "validate_python"):
        return "validate"
    if pkg in QUIET_PKGS or pkg in STDLIB:
        return None
    return "lib"


def method_effect(attr, call, imports, recv_text):
    """A method on something whose type we can't see (`df.to_csv(...)`): judged by its name, and by what the file
    imports where the name alone is too common."""
    if attr in METHOD_WRITE:
        return "file-write", "python"
    if attr in METHOD_READ:
        return "file-read", "python"
    if attr == "open" and re.search(r"(path|file|p)$", recv_text.lower() or ""):
        return file_mode(call, 0), "pathlib"
    if attr in ("unlink", "rmdir") and imports & {"pathlib", "os"}:
        return "file-write", "pathlib"
    if "ee" in imports and attr in ("getInfo", "computePixels", "getDownloadURL", "getThumbURL"):
        return "network", "ee"
    if "cdsapi" in imports and attr == "retrieve":
        return "network", "cdsapi"
    if imports & {"requests", "httpx"} and attr in HTTP_VERBS and re.search(r"(session|client|http|^s$)", recv_text.lower()):
        return "network", "requests" if "requests" in imports else "httpx"
    if imports & {"sqlite3", "psycopg", "psycopg2", "pymysql", "duckdb", "sqlalchemy"} and attr in ("execute", "executemany", "executescript"):
        return "db-raw", next(iter(sorted(imports & {"sqlite3", "psycopg", "psycopg2", "pymysql", "duckdb", "sqlalchemy"})))
    if "pymongo" in imports and attr in ("find", "find_one", "aggregate", "count_documents"):
        return "db-read", "pymongo"
    if "pymongo" in imports and attr in ("insert_one", "insert_many", "update_one", "update_many", "delete_one", "delete_many", "replace_one"):
        return "db-write", "pymongo"
    if "smtplib" in imports and attr in ("sendmail", "send_message"):
        return "email", "smtplib"
    if "boto3" in imports and attr in ("upload_file", "download_file", "put_object", "get_object", "upload_fileobj", "download_fileobj"):
        return "storage", "boto3"
    if attr in ("warning", "error", "exception", "critical") and re.search(r"(^|_)(log|logger)$", recv_text.lower()):
        return "log", "logging"
    if attr == "to_sql":
        return "db-write", "pandas"
    return None, None


def file_mode(call, idx):
    mode = None
    if call is not None:
        if len(call.args) > idx and isinstance(call.args[idx], ast.Constant) and isinstance(call.args[idx].value, str):
            mode = call.args[idx].value
        for k in call.keywords:
            if k.arg == "mode" and isinstance(k.value, ast.Constant) and isinstance(k.value.value, str):
                mode = k.value.value
    return "file-write" if mode and re.search(r"[wax+]", mode) else "file-read"


# ------------------------------------------------------------------ text helpers
def squash(s):
    return re.sub(r"\s+", " ", s or "").strip()


def cut(s, n):
    return s if len(s) <= n else s[: n - 1] + "…"


class Text:
    def __init__(self, text):
        self.text = text
        self.lines = text.split("\n")
        self._bytes = None

    def seg(self, node):
        """The exact source of a node. ast's own get_source_segment re-splits the whole file on every call, which
        is far too slow over thousands of nodes; offsets are UTF-8 bytes, so slice encoded lines instead."""
        s = None
        try:
            if self._bytes is None:
                self._bytes = [ln.encode("utf-8") for ln in self.lines]
            l1, l2 = node.lineno - 1, node.end_lineno - 1
            c1, c2 = node.col_offset, node.end_col_offset
            if l1 == l2:
                s = self._bytes[l1][c1:c2].decode("utf-8", errors="replace")
            else:
                parts = [self._bytes[l1][c1:], *self._bytes[l1 + 1:l2], self._bytes[l2][:c2]]
                s = b"\n".join(parts).decode("utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            s = None
        if s is None and hasattr(ast, "unparse"):
            try:
                s = ast.unparse(node)
            except Exception:  # noqa: BLE001
                s = ""
        return s or ""

    def short(self, node, n=90):
        return cut(squash(self.seg(node)), n) if node is not None else ""


def clean_doc(doc):
    """A docstring as plain markdown: summary paragraphs joined, indented usage lines as a list, and the
    parameter sections taken out (returned separately)."""
    if not doc:
        return "", {}
    params = {}
    out = []
    lines = doc.expandtabs().split("\n")
    i = 0
    section = None
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        # Google style: "Args:" then indented "name (type): text"
        if re.match(r"^(Args|Arguments|Parameters|Params|Keyword Args|Keyword Arguments|Other Parameters):\s*$", s):
            section = "params"
            i += 1
            continue
        if re.match(r"^(Returns|Return|Yields|Raises|Examples?|Notes?|See Also|References|Attributes)\s*:?\s*$", s) and (
            s.endswith(":") or (i + 1 < len(lines) and re.match(r"^-{3,}$", lines[i + 1].strip()))
        ):
            section = "skip" if not s.startswith(("Example", "Note")) else None
            if i + 1 < len(lines) and re.match(r"^-{3,}$", lines[i + 1].strip()):
                i += 1
            if section is None:
                out.append(f"**{s.rstrip(':')}**")
            i += 1
            continue
        # NumPy style: "Parameters" underlined with dashes
        if s in ("Parameters", "Other Parameters") and i + 1 < len(lines) and re.match(r"^-{3,}$", lines[i + 1].strip()):
            section = "nparams"
            i += 2
            continue
        m = re.match(r"^:param\s+(?:[\w\[\], ]+\s+)?(\*{0,2}\w+):\s*(.*)$", s)
        if m:
            params[m.group(1)] = m.group(2)
            i += 1
            continue
        if re.match(r"^:(type|rtype|returns?|raises?)\b", s):
            i += 1
            continue
        if section == "params":
            if not s:
                section = None
                out.append("")
                i += 1
                continue
            m = re.match(r"^(\*{0,2}\w+)\s*(\([^)]*\))?\s*:\s*(.*)$", s)
            if m and line.startswith((" ", "\t")):
                params[m.group(1).lstrip("*")] = m.group(3)
                last = m.group(1).lstrip("*")
                i += 1
                while i < len(lines) and lines[i].strip() and len(lines[i]) - len(lines[i].lstrip()) > len(line) - len(line.lstrip()):
                    params[last] += " " + lines[i].strip()
                    i += 1
                continue
            if not line.startswith((" ", "\t")):
                section = None
                continue
            i += 1
            continue
        if section == "nparams":
            if not s:
                i += 1
                if i < len(lines) and lines[i].strip() and not lines[i].startswith(" "):
                    continue
                section = None
                continue
            m = re.match(r"^(\*{0,2}\w+)\s*(?::\s*(.*))?$", s)
            if m and not line.startswith(" "):
                name = m.group(1).lstrip("*")
                params[name] = ""
                i += 1
                while i < len(lines) and lines[i].startswith((" ", "\t")) and lines[i].strip():
                    params[name] = (params[name] + " " + lines[i].strip()).strip()
                    i += 1
                continue
            section = None
            continue
        if section == "skip":
            if not s or line.startswith((" ", "\t")) or re.match(r"^-{3,}$", s):
                i += 1
                continue
            section = None
            continue
        out.append(line)
        i += 1
    # Paragraphs: banner lines dropped, indented lines (usage, examples) become list items.
    paras = []
    cur = []
    listed = 0
    for line in out:
        s = line.strip()
        if re.fullmatch(r"[═─━=\-_*~#·•]{4,}", s or "x"):
            continue
        if not s:
            if cur:
                paras.append(" ".join(cur))
                cur = []
            continue
        if line.startswith(("    ", "\t")) or s.startswith(("$ ", ">>> ")):
            if cur:
                paras.append(" ".join(cur))
                cur = []
            if listed < 12:
                raw = re.sub(r"^(\$|>>>)\s+", "", s)
                code, sep, note = raw.partition("  #")
                if not sep:
                    code, sep, note = raw.partition(" # ")
                if sep:  # a command and its comment
                    item = f"- `{squash(code).replace('`', chr(39))}`" + (f" ({squash(note).lstrip('# ')})" if note.strip(" #") else "")
                else:
                    cols = re.split(r"\s{2,}", raw, maxsplit=1)
                    if len(cols) == 2 and len(cols[0]) <= 40:  # a two-column layout: name, then what it is
                        item = f"- `{cols[0].replace('`', chr(39))}` {squash(cols[1])}"
                    else:
                        item = f"- `{squash(raw).replace('`', chr(39))}`"
                paras.append(item)
                listed += 1
            continue
        if re.fullmatch(r"[A-Z0-9][A-Z0-9 ,'’()/&?—-]{6,80}", s) and re.search(r"[A-Z]{3}", s):
            if cur:
                paras.append(" ".join(cur))
                cur = []
            paras.append(f"**{s.capitalize()}**")
            continue
        if re.match(r"^[-*•]\s+", s):
            if cur:
                paras.append(" ".join(cur))
                cur = []
            paras.append("- " + re.sub(r"^[-*•]\s+", "", s))
            continue
        cur.append(s)
    if cur:
        paras.append(" ".join(cur))
    text = ""
    for p in paras:
        sep = "\n" if p.startswith("- ") and text.split("\n")[-1].startswith("- ") else "\n\n"
        nxt = (text + sep + p) if text else p
        if len(nxt) > MAX_DOC:
            text = text + "\n\n…" if text else cut(p, MAX_DOC)
            break
        text = nxt
    return text.strip(), {k: squash(v) for k, v in params.items() if v}


def comment_above(text, line):
    """`#` comment lines directly above a line (1-based), for code with no docstring."""
    lines = text.lines
    i = line - 2
    got = []
    while i >= 0 and lines[i].strip().startswith("#") and not lines[i].strip().startswith("#!"):
        got.insert(0, lines[i].strip().lstrip("#").strip())
        i -= 1
    return squash(" ".join(got))


# ------------------------------------------------------------------ modules and imports
class Mod:
    def __init__(self, file, text, tree):
        self.file = file
        self.text = Text(text)
        self.tree = tree
        parts = file[:-3].split("/")
        self.is_pkg = parts[-1] == "__init__"
        if self.is_pkg:
            parts = parts[:-1]
        self.dotted = ".".join(parts)
        self.dir = "/".join(file.split("/")[:-1])
        self.names = {}        # top-level name -> binding
        self.symbols = {}      # top-level name -> symbol id
        self.extra_roots = []  # folders this file adds to sys.path
        self.imports_int = set()
        self.imports_ext = set()
        self.import_pkgs = set()
        self.all = None
        self.is_test = False


def join_path(*parts):
    out = []
    for p in "/".join(x for x in parts if x).split("/"):
        if p in ("", "."):
            continue
        if p == "..":
            if not out:
                return None
            out.pop()
        else:
            out.append(p)
    return "/".join(out)


class Index:
    def __init__(self, mods, files, extra_paths):
        self.mods = mods
        self.by_file = {m.file: m for m in mods}
        self.files = files
        self.dirs = {"/".join(f.split("/")[:i]) for f in files for i in range(1, f.count("/") + 1)}
        self.extra_paths = extra_paths
        self.cache = {}

    def find(self, dotted, frm):
        """The file (or package folder) a dotted import names, seen from file `frm`."""
        key = (dotted, frm.file)
        if key in self.cache:
            return self.cache[key]
        rel = dotted.replace(".", "/")
        roots = [frm.dir, *frm.extra_roots, *self.extra_paths, ""]
        hit = None
        for r in roots:
            if r is None:
                continue
            base = join_path(r, rel)
            if base is None:
                continue
            if base + ".py" in self.by_file:
                hit = ("mod", base + ".py")
                break
            if base + "/__init__.py" in self.by_file:
                hit = ("mod", base + "/__init__.py")
                break
            if base in self.dirs and r != "":
                hit = ("pkgdir", base)
                break
        if hit is None and dotted.split(".")[0] not in STDLIB:
            # The same name somewhere else in the repo, nearest folder first.
            here = frm.dir.split("/") if frm.dir else []
            cands = [m for m in self.mods if m.dotted == dotted or m.dotted.endswith("." + dotted)]
            if cands:
                def score(m):
                    d = m.dir.split("/") if m.dir else []
                    common = 0
                    for a, b in zip(here, d):
                        if a != b:
                            break
                        common += 1
                    return (-common, len(m.file), m.file)
                hit = ("mod", sorted(cands, key=score)[0].file)
            elif rel in self.dirs:
                hit = ("pkgdir", rel)
        self.cache[key] = hit
        return hit


def eval_path(node, env, file, depth=0):
    """A sys.path entry built from __file__ (`Path(__file__).resolve().parents[1] / "build"`), as a repo path."""
    if depth > 8 or node is None:
        return None
    if isinstance(node, ast.Name):
        if node.id == "__file__":
            return ("file", file)
        if node.id in env:
            return eval_path(env[node.id], env, file, depth + 1)
        return None
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return ("dir", node.value)
    if isinstance(node, ast.Call):
        f = node.func
        name = f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else ""
        if name in ("str", "Path", "PurePath", "fspath", "abspath", "realpath", "normpath") and node.args:
            return eval_path(node.args[0], env, file, depth + 1)
        if name in ("resolve", "absolute") and isinstance(f, ast.Attribute):
            return eval_path(f.value, env, file, depth + 1)
        if name == "dirname" and node.args:
            v = eval_path(node.args[0], env, file, depth + 1)
            return up(v, 1)
        if name == "join" and node.args:
            v = eval_path(node.args[0], env, file, depth + 1)
            for a in node.args[1:]:
                if isinstance(a, ast.Constant) and isinstance(a.value, str) and v:
                    v = ("dir", join_path(as_dir(v), a.value))
                else:
                    return None
            return v
        return None
    if isinstance(node, ast.Attribute) and node.attr == "parent":
        return up(eval_path(node.value, env, file, depth + 1), 1)
    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute) and node.value.attr == "parents":
        sl = slice_of(node)
        if isinstance(sl, ast.Constant) and isinstance(sl.value, int):
            return up(eval_path(node.value.value, env, file, depth + 1), sl.value + 1)
        return None
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        v = eval_path(node.left, env, file, depth + 1)
        if v and isinstance(node.right, ast.Constant) and isinstance(node.right.value, str):
            return ("dir", join_path(as_dir(v), node.right.value))
        return None
    return None


def as_dir(v):
    return "/".join(v[1].split("/")[:-1]) if v[0] == "file" else v[1]


def up(v, n):
    if v is None:
        return None
    d = as_dir(v) if v[0] == "file" else v[1]
    n = n - 1 if v[0] == "file" else n
    for _ in range(n):
        if d is None:
            return None
        d = join_path(d, "..") if d else None
    return ("dir", d) if d is not None else None


# ------------------------------------------------------------------ the scanner
class Scanner:
    def __init__(self, req):
        self.root = req["root"]
        self.req = req
        self.readers = set(req.get("envReaders") or [])
        self.warnings = []
        self.symbols = []
        self.by_id = {}
        self.entries = {}
        self.tests = {}
        self.sources = {}
        self.imports = {}

    # ---------------------------------------------------------------- pass 0: parse
    def load(self):
        mods = []
        cfg = self.req.get("config") or {}
        include = cfg.get("include") or []
        exclude = cfg.get("exclude") or []
        generated = set(self.req.get("generated") or [])

        def matches(f, rule):
            return re.search(rule[1:-1], f) is not None if rule.startswith("/") and rule.endswith("/") else f.startswith(rule)

        for f in self.req["files"]:
            if not f.endswith(".py") or SKIP.search(f) or f in generated:
                continue
            if include and not any(matches(f, r) for r in include):
                continue
            if any(matches(f, r) for r in exclude):
                continue
            path = os.path.join(self.root, *f.split("/"))
            try:
                if os.path.getsize(path) > 1_500_000:
                    continue
                with open(path, "rb") as fh:
                    text = fh.read().decode("utf-8", errors="replace").replace("\r\n", "\n")
                tree = ast.parse(text, filename=f)
            except SyntaxError as e:
                self.warnings.append(f"code map: {f} doesn't parse as Python ({e.msg}, line {e.lineno}); skipped")
                continue
            except Exception as e:  # noqa: BLE001
                self.warnings.append(f"code map: {f} couldn't be read ({type(e).__name__}); skipped")
                continue
            m = Mod(f, text, tree)
            m.is_test = bool(TEST_PATH.search(f)) and (
                re.search(r"^\s*(import|from)\s+(pytest|unittest)\b", text, re.M) is not None
                or re.search(r"(^|/)(tests?|testing)/", f) is not None
                or f.endswith("conftest.py")
            )
            mods.append(m)
        self.mods = mods
        self.index = Index(mods, [m.file for m in mods], cfg.get("paths") or [])

    # ---------------------------------------------------------------- pass 1: names, imports, declarations
    def bind_imports(self, m, stmt, names):
        if isinstance(stmt, ast.Import):
            for a in stmt.names:
                top = a.name.split(".")[0]
                hit = self.index.find(a.name, m)
                if hit and hit[0] == "mod":
                    m.imports_int.add(hit[1])
                    if a.asname or "." not in a.name:
                        names[a.asname or a.name] = ("mod", hit[1])
                    else:
                        names[top] = ("dotted", top, m.file)
                elif hit and hit[0] == "pkgdir":
                    names[a.asname or top] = ("dotted", a.name if a.asname else top, m.file)
                else:
                    m.imports_ext.add(top)
                    m.import_pkgs.add(top)
                    names[a.asname or top] = ("ext", top, a.name if a.asname else top)
        elif isinstance(stmt, ast.ImportFrom):
            if stmt.level:
                # `from . import x` is relative to the file's own folder, for modules and packages alike
                base = m.dir.split("/") if m.dir else []
                up_n = stmt.level - 1
                if up_n > len(base):
                    return
                base = base[: len(base) - up_n]
                target = "/".join(base + (stmt.module.split(".") if stmt.module else []))
                hit = ("mod", target + ".py") if target + ".py" in self.index.by_file else (
                    ("mod", target + "/__init__.py") if target + "/__init__.py" in self.index.by_file else (
                        ("pkgdir", target) if target in self.index.dirs or not target else None))
                modname = None
            else:
                hit = self.index.find(stmt.module, m)
                modname = stmt.module
            for a in stmt.names:
                local = a.asname or a.name
                if a.name == "*":
                    if hit and hit[0] == "mod":
                        m.imports_int.add(hit[1])
                        names.setdefault("*", []).append(hit[1])
                    elif modname:
                        m.imports_ext.add(modname.split(".")[0])
                        m.import_pkgs.add(modname.split(".")[0])
                    continue
                if hit:
                    sub = None
                    pkg_dir = hit[1][: -len("/__init__.py")] if hit[0] == "mod" and hit[1].endswith("/__init__.py") else hit[1] if hit[0] == "pkgdir" else None
                    if pkg_dir is not None:
                        sub = join_path(pkg_dir, a.name)
                        if sub + ".py" in self.index.by_file:
                            names[local] = ("mod", sub + ".py")
                            m.imports_int.add(sub + ".py")
                            continue
                        if sub + "/__init__.py" in self.index.by_file:
                            names[local] = ("mod", sub + "/__init__.py")
                            m.imports_int.add(sub + "/__init__.py")
                            continue
                    if hit[0] == "mod":
                        m.imports_int.add(hit[1])
                        names[local] = ("ref", hit[1], a.name)
                        continue
                if modname:
                    top = modname.split(".")[0]
                    m.imports_ext.add(top)
                    m.import_pkgs.add(top)
                    names[local] = ("ext", top, f"{modname}.{a.name}")

    def declare(self):
        for m in self.mods:
            env = {}
            # sys.path entries the file adds, so `import grid` finds the right grid.py
            for st in m.tree.body:
                if isinstance(st, ast.Assign) and len(st.targets) == 1 and isinstance(st.targets[0], ast.Name):
                    env[st.targets[0].id] = st.value
            for node in ast.walk(m.tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in ("insert", "append") \
                        and isinstance(node.func.value, ast.Attribute) and node.func.value.attr == "path":
                    arg = node.args[-1] if node.args else None
                    v = eval_path(arg, env, m.file)
                    if v:
                        d = as_dir(v) if v[0] == "file" else v[1]
                        if d is not None and d not in m.extra_roots:
                            m.extra_roots.append(d)
        for m in self.mods:
            names = {}
            for st in self.top_statements(m.tree.body):
                if isinstance(st, (ast.Import, ast.ImportFrom)):
                    self.bind_imports(m, st, names)
                elif isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    names[st.name] = ("sym", f"{m.file}#{st.name}")
                elif isinstance(st, (ast.Assign, ast.AnnAssign)):
                    targets = st.targets if isinstance(st, ast.Assign) else [st.target]
                    for t in targets:
                        for n in ast.walk(t):
                            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
                                names.setdefault(n.id, ("value", f"{m.file}#{n.id}"))
                    if isinstance(st, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in st.targets):
                        try:
                            m.all = set(ast.literal_eval(st.value))
                        except Exception:  # noqa: BLE001
                            pass
            m.names = names

    @staticmethod
    def top_statements(body):
        """Top-level statements, looking inside `if`/`try` blocks that only set things up (imports, defs)."""
        for st in body:
            yield st
            if isinstance(st, ast.If) or isinstance(st, ast.Try) or (hasattr(ast, "TryStar") and isinstance(st, getattr(ast, "TryStar"))):
                inner = list(st.body) + list(getattr(st, "orelse", []))
                for h in getattr(st, "handlers", []):
                    inner += h.body
                for s in inner:
                    if isinstance(s, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        yield s

    # ---------------------------------------------------------------- resolution
    def binding_in(self, mfile, name, depth=0):
        m = self.index.by_file.get(mfile)
        if not m or depth > 6:
            return None
        b = m.names.get(name)
        if b is None:
            for star in m.names.get("*", []) if isinstance(m.names.get("*"), list) else []:
                r = self.binding_in(star, name, depth + 1)
                if r:
                    return r
            if m.is_pkg:
                sub = join_path(m.dir, name)
                if sub + ".py" in self.index.by_file:
                    return ("mod", sub + ".py")
            return None
        return self.settle(b, depth)

    def settle(self, b, depth=0):
        if b[0] == "ref":
            r = self.binding_in(b[1], b[2], depth + 1)
            return r if r else ("unknown",)
        if b[0] in ("sym", "value"):
            return ("sym", b[1]) if b[1] in self.by_id else ("unknown",)
        return b

    def method_of(self, cls_id, attr, depth=0):
        if depth > 4:
            return None
        mid = f"{cls_id}.{attr}"
        if mid in self.by_id:
            return mid
        cls = self.by_id.get(cls_id)
        for base_id in (cls or {}).get("_bases", []):
            r = self.method_of(base_id, attr, depth + 1)
            if r:
                return r
        return None

    # ---------------------------------------------------------------- pass 2: symbols
    def add(self, sym, node, mod, fn=None, extra=None):
        start = min([node.lineno] + [d.lineno for d in getattr(node, "decorator_list", [])])
        sym["line"] = start
        sym["end"] = getattr(node, "end_lineno", node.lineno) or node.lineno
        sym["_node"] = node
        sym["_fn"] = fn
        sym["_mod"] = mod
        if extra:
            sym.update(extra)
        self.symbols.append(sym)
        self.by_id[sym["id"]] = sym
        return sym

    def doc_for(self, node, mod):
        doc = ast.get_docstring(node, clean=True) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)) else None
        if doc:
            return clean_doc(doc)
        line = min([node.lineno] + [d.lineno for d in getattr(node, "decorator_list", [])])
        return comment_above(mod.text, line), {}

    def exported(self, name, mod):
        if name.startswith("_"):
            return False
        return mod.all is None or name in mod.all

    def collect(self):
        for m in self.mods:
            if m.is_test:
                continue
            self.sources[m.file] = m.text.text
            for st in self.top_statements(m.tree.body):
                if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self.add_function(st, m, f"{m.file}#{st.name}", None)
                elif isinstance(st, ast.ClassDef):
                    self.add_class(st, m)
        # values, after functions and classes so a later `x = SomeClass()` can be typed
        for m in self.mods:
            if m.is_test:
                continue
            m.program = self.is_program(m)
            if m.program:
                continue
            for st in m.tree.body:
                target = value = ann = None
                if isinstance(st, ast.Assign) and len(st.targets) == 1 and isinstance(st.targets[0], ast.Name):
                    target, value = st.targets[0].id, st.value
                elif isinstance(st, ast.AnnAssign) and isinstance(st.target, ast.Name) and st.value is not None:
                    target, value, ann = st.target.id, st.value, st.annotation
                if not target or (target.startswith("__") and target.endswith("__")):
                    continue
                sid = f"{m.file}#{target}"
                if sid in self.by_id:
                    continue
                doc, _ = self.doc_for(st, m)
                if isinstance(value, ast.Lambda):
                    self.add_function(value, m, sid, None, name=target, stmt=st)
                    continue
                kind = "object" if isinstance(value, (ast.Dict, ast.List, ast.Set, ast.Tuple, ast.ListComp, ast.DictComp, ast.SetComp)) else "value"
                sym = {"id": sid, "name": target, "file": m.file, "kind": kind, "exported": self.exported(target, m), "doc": doc,
                       "value": m.text.short(value, 160)}
                if ann is not None:
                    sym["declared"] = m.text.short(ann, 120)
                self.add(sym, st, m, extra={"_value": value})

    def add_function(self, node, m, sid, parent, name=None, stmt=None, method_of=None):
        name = name or node.name
        doc, dparams = self.doc_for(stmt or node, m)
        sym = {"id": sid, "name": name, "file": m.file, "kind": "method" if method_of else "function",
               "doc": doc, "_dparams": dparams}
        if parent:
            sym["parent"] = parent
        if method_of:
            sym["parent"] = method_of
        if isinstance(node, ast.AsyncFunctionDef):
            sym["async"] = True
        if not parent and not method_of:
            sym["exported"] = self.exported(name, m)
        elif method_of:
            sym["exported"] = not name.startswith("_") or (name.startswith("__") and name.endswith("__"))
        decos = getattr(node, "decorator_list", [])
        wrappers = [d for d in decos if not self.entry_decorator(d, m)]
        if wrappers:
            sym["wrapper"] = "@" + m.text.short(wrappers[0], 60)
        self.add(sym, stmt or node, m, fn=node)
        if not isinstance(node, ast.Lambda):
            self.collect_inner(sym, node, m)
        return sym

    def collect_inner(self, parent, fn, m):
        for st in self.walk_shallow(fn.body):
            if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef)):
                s = self.add_function(st, m, f"{parent['id']}.{st.name}", parent["id"])
                s["exported"] = False

    @staticmethod
    def walk_shallow(body):
        """Statements in a body, nested blocks included, but not inside other functions or classes."""
        stack = list(reversed(body))
        while stack:
            st = stack.pop()
            yield st
            if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                continue
            for field in ("body", "orelse", "finalbody", "handlers", "cases"):
                for child in reversed(getattr(st, field, []) or []):
                    if isinstance(child, ast.AST):
                        stack.append(child)

    def add_class(self, node, m):
        doc, _ = self.doc_for(node, m)
        sid = f"{m.file}#{node.name}"
        deco_names = {m.text.short(d, 40).split("(")[0].split(".")[-1] for d in node.decorator_list}
        base_names = [m.text.short(b, 60) for b in node.bases]
        is_type = bool(deco_names & {"dataclass", "define", "frozen", "s", "attrs", "dataclass_json"}) or any(
            re.search(r"(^|\.)(TypedDict|NamedTuple|Enum|IntEnum|StrEnum|Flag|IntFlag|BaseModel|Protocol|Struct)$", b) for b in base_names)
        sym = {"id": sid, "name": node.name, "file": m.file, "kind": "type" if is_type else "class",
               "exported": self.exported(node.name, m), "doc": doc}
        if base_names:
            sym["extends"] = ", ".join(base_names)
        members = []
        is_enum = any(re.search(r"(Enum|Flag)$", b) for b in base_names)
        for st in node.body:
            if isinstance(st, ast.AnnAssign) and isinstance(st.target, ast.Name):
                members.append({"name": st.target.id, "type": m.text.short(st.annotation, 140),
                                **({"opt": True} if st.value is not None else {}),
                                **({"doc": c} if (c := self.inline_comment(m, st)) else {})})
            elif is_enum and isinstance(st, ast.Assign) and len(st.targets) == 1 and isinstance(st.targets[0], ast.Name):
                members.append({"name": st.targets[0].id, "type": m.text.short(st.value, 40)})
        if members:
            sym["members"] = members
        cls = self.add(sym, node, m, extra={"_bases_nodes": node.bases})
        for st in node.body:
            if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.add_function(st, m, f"{sid}.{st.name}", None, method_of=sid)
        return cls

    @staticmethod
    def inline_comment(m, st):
        line = m.text.lines[st.lineno - 1] if st.lineno - 1 < len(m.text.lines) else ""
        if "#" in line:
            c = line.split("#", 1)[1].strip()
            return c if c and not c.startswith(("type:", "noqa")) else ""
        return ""

    def is_program(self, m):
        """True when the file's top level is the program itself (a Streamlit page, a plain script) rather than
        declarations plus a `__main__` block."""
        for st in m.tree.body:
            if isinstance(st, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Assign, ast.AnnAssign, ast.Pass)):
                continue
            if isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant):
                continue
            if self.is_main_guard(st) or self.is_setup_only(st):
                continue
            return True
        return False

    @staticmethod
    def is_main_guard(st):
        if not isinstance(st, ast.If) or not isinstance(st.test, ast.Compare):
            return False
        parts = [st.test.left, *st.test.comparators]
        return any(isinstance(p, ast.Name) and p.id == "__name__" for p in parts) and any(
            isinstance(p, ast.Constant) and p.value == "__main__" for p in parts)

    @staticmethod
    def is_setup_only(st):
        """sys.path tweaks, warning filters, `if TYPE_CHECKING:`, guarded imports: setup, not the program."""
        if isinstance(st, ast.Expr) and isinstance(st.value, ast.Call):
            t = ast.dump(st.value.func)
            return "'path'" in t or "filterwarnings" in t or "simplefilter" in t or "load_dotenv" in t or "set_option" in t or "basicConfig" in t
        if isinstance(st, ast.If) and isinstance(st.test, (ast.Name, ast.Attribute)) and "TYPE_CHECKING" in ast.dump(st.test):
            return True
        if isinstance(st, ast.Try):
            return all(isinstance(s, (ast.Import, ast.ImportFrom, ast.Assign, ast.Pass, ast.Expr)) for s in st.body)
        return False

    # ---------------------------------------------------------------- pass 3: outlines
    def scope_for(self, sym):
        """Names a function can see: its parameters and locals, its enclosing functions, then the module."""
        chain = []
        cur = sym
        while cur is not None:
            fn = cur.get("_fn")
            if fn is not None and not isinstance(fn, ast.ClassDef):
                chain.append(self.locals_of(cur, fn))
            cur = self.by_id.get(cur.get("parent")) if cur.get("parent") and self.by_id.get(cur.get("parent"), {}).get("kind") not in ("class", "type") else None
        return chain

    def locals_of(self, sym, fn):
        if "_locals" in sym:
            return sym["_locals"]
        m = sym["_mod"]
        names = {}
        args = fn.args
        all_args = [*getattr(args, "posonlyargs", []), *args.args, *([args.vararg] if args.vararg else []), *args.kwonlyargs, *([args.kwarg] if args.kwarg else [])]
        for a in all_args:
            t = None
            if a.annotation is not None:
                t = self.type_of_annotation(a.annotation, m)
            names[a.arg] = ("param", a.arg, t)
        if sym.get("kind") == "method" and all_args:
            first = all_args[0].arg
            names[first] = ("self", sym["parent"])
        body = fn.body if isinstance(fn.body, list) else []
        for st in self.walk_shallow(body):
            if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef)):
                names[st.name] = ("sym", f"{sym['id']}.{st.name}")
            elif isinstance(st, (ast.Import, ast.ImportFrom)):
                self.bind_imports(m, st, names)
        for node in self.walk_expr_nodes(body):
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                typ = self.type_of_value(node.value, m, names) if getattr(node, "value", None) is not None else None
                for t in targets:
                    for n in ast.walk(t):
                        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store) and names.get(n.id, ("",))[0] not in ("sym", "self", "mod", "ext", "dotted"):
                            names[n.id] = ("local", n.id, typ if isinstance(t, ast.Name) else None)
            elif isinstance(node, (ast.For, ast.AsyncFor, ast.comprehension)):
                for n in ast.walk(node.target):
                    if isinstance(n, ast.Name):
                        names.setdefault(n.id, ("local", n.id, None))
            elif isinstance(node, ast.withitem) and node.optional_vars is not None:
                for n in ast.walk(node.optional_vars):
                    if isinstance(n, ast.Name):
                        names.setdefault(n.id, ("local", n.id, None))
            elif isinstance(node, ast.ExceptHandler) and node.name:
                names.setdefault(node.name, ("local", node.name, None))
            elif isinstance(node, (ast.Global, ast.Nonlocal)):
                for n in node.names:
                    names.pop(n, None)
        sym["_locals"] = names
        return names

    @staticmethod
    def walk_expr_nodes(body):
        """Every node in a body except inside nested functions, lambdas and classes."""
        stack = list(body)
        while stack:
            n = stack.pop()
            yield n
            for c in ast.iter_child_nodes(n):
                if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                    continue
                stack.append(c)

    def type_of_annotation(self, ann, m):
        node = ann
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            try:
                node = ast.parse(node.value, mode="eval").body
            except SyntaxError:
                return None
        if isinstance(node, ast.Subscript):  # Optional[X]
            node = slice_of(node)
        if isinstance(node, ast.BinOp):  # X | None
            node = node.left
        r = self.resolve_static(node, m)
        return r[1] if r and r[0] == "sym" and self.by_id.get(r[1], {}).get("kind") in ("class", "type") else None

    def type_of_value(self, value, m, names=None):
        """The class a value is an instance of, when we can see it: `OurClass(...)`, or a call to one of our
        functions whose return annotation names one of our classes."""
        if isinstance(value, ast.Await):
            value = value.value
        if isinstance(value, ast.Call):
            r = self.resolve_static(value.func, m, names)
            if r and r[0] == "sym":
                target = self.by_id.get(r[1], {})
                if target.get("kind") in ("class", "type"):
                    return r[1]
                fn = target.get("_fn")
                if fn is not None and getattr(fn, "returns", None) is not None:
                    return self.type_of_annotation(fn.returns, target["_mod"])
        return None

    def resolve_static(self, node, m, names=None):
        """Resolve a Name/Attribute using module names (and optional local names), without a full scope."""
        if isinstance(node, ast.Name):
            b = (names or {}).get(node.id) or m.names.get(node.id)
            if b is None:
                return ("builtin", node.id) if node.id in BUILTIN_NAMES else None
            if b[0] == "self":
                return ("inst", b[1])
            if b[0] in ("param", "local"):
                return ("inst", b[2]) if b[2] else None
            return self.settle(b)
        if isinstance(node, ast.Attribute):
            base = self.resolve_static(node.value, m, names)
            return self.attr_of(base, node.attr)
        return None

    def attr_of(self, base, attr):
        if base is None:
            return None
        if base[0] == "mod":
            r = self.binding_in(base[1], attr)
            return r
        if base[0] == "pkgdir":
            sub = join_path(base[1], attr)
            if sub + ".py" in self.index.by_file:
                return ("mod", sub + ".py")
            if sub + "/__init__.py" in self.index.by_file:
                return ("mod", sub + "/__init__.py")
            if sub in self.index.dirs:
                return ("pkgdir", sub)
            return None
        if base[0] == "dotted":
            # `import a.b` then `a.b.c.f()`: walk down until the dotted name is a module, then look inside it
            frm = self.index.by_file.get(base[2])
            if frm is None:
                return None
            here = self.index.find(base[1], frm)
            if here and here[0] == "mod":
                r = self.binding_in(here[1], attr)
                if r:
                    return r
            dotted = f"{base[1]}.{attr}"
            hit = self.index.find(dotted, frm)
            return ("mod", hit[1]) if hit and hit[0] == "mod" else ("dotted", dotted, base[2])
        if base[0] == "sym":
            s = self.by_id.get(base[1])
            if s and s.get("kind") in ("class", "type"):
                mid = self.method_of(base[1], attr)
                return ("sym", mid) if mid else None
            if s and s.get("_vtype"):
                mid = self.method_of(s["_vtype"], attr)
                return ("sym", mid) if mid else None
            return None
        if base[0] == "ext":
            return ("ext", base[1], f"{base[2]}.{attr}")
        if base[0] == "inst":
            mid = self.method_of(base[1], attr)
            return ("sym", mid) if mid else None
        return None

    def lookup(self, name, ctx):
        for scope in ctx["scopes"]:
            if name in scope:
                b = scope[name]
                return self.settle(b) if b[0] in ("ref", "value") else b
        b = ctx["mod"].names.get(name)
        if b is not None:
            return self.settle(b)
        for star in ctx["mod"].names.get("*", []) if isinstance(ctx["mod"].names.get("*"), list) else []:
            r = self.binding_in(star, name)
            if r:
                return r
        if name in BUILTIN_NAMES:
            return ("ext", "builtins", name)
        return None

    def resolve(self, node, ctx):
        """What a name or attribute chain refers to: one of our symbols, a parameter, a module, or a library."""
        if isinstance(node, ast.Name):
            b = self.lookup(node.id, ctx)
            if b is None:
                return None
            if b[0] == "param":
                return ("param", b[1], b[2])
            if b[0] == "local":
                return ("local", b[1], b[2])
            if b[0] == "self":
                return ("self", b[1])
            if b[0] in ("sym", "value"):
                return ("sym", b[1]) if b[1] in self.by_id else None
            return b
        if isinstance(node, ast.Attribute):
            base = self.resolve(node.value, ctx)
            if base is None:
                return ("unknown-attr", node.attr)
            if base[0] in ("param", "local") and base[2]:
                mid = self.method_of(base[2], node.attr)
                return ("sym", mid) if mid else ("unknown-attr", node.attr)
            if base[0] == "self":
                mid = self.method_of(base[1], node.attr)
                return ("sym", mid) if mid else ("unknown-attr", node.attr)
            if base[0] in ("param", "local", "unknown-attr", "unknown"):
                return ("unknown-attr", node.attr)
            r = self.attr_of(base, node.attr)
            return r if r else ("unknown-attr", node.attr)
        return None

    # ---------------------------------------------------------------- steps
    def note(self, ctx, step):
        ctx["count"] += 1
        return step

    def link(self, ctx, sid, how):
        if sid == ctx["sym"]["id"]:
            return
        prev = ctx["links"].get(sid)
        if not prev or (prev != "call" and how == "call"):
            ctx["links"][sid] = how

    def stmts(self, body, ctx):
        out = []
        for st in body:
            if ctx["count"] > MAX_STEPS:
                out.append({"t": "more"})
                break
            out.extend(self.stmt(st, ctx))
        return out

    def cond(self, node, ctx):
        was = ctx["cond"]
        ctx["cond"] = True
        out = self.expr(node, ctx)
        ctx["cond"] = was
        return out

    def stmt(self, s, ctx):
        T = ctx["mod"].text
        if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom, ast.Pass,
                          ast.Global, ast.Nonlocal)):
            return []
        if isinstance(s, ast.Expr):
            if isinstance(s.value, ast.Constant):
                return []
            return self.expr(s.value, ctx)
        if isinstance(s, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            value = s.value
            if value is None:
                return []
            steps = self.expr(value, ctx)
            target = value.value if isinstance(value, ast.Await) else value
            targets = s.targets if isinstance(s, ast.Assign) else [s.target]
            for st in steps:
                if st.get("_n") is target:
                    st["as"] = cut(", ".join(T.short(t, 50) for t in targets), 50)
                    break
            return steps
        if isinstance(s, ast.If):
            if Scanner.is_main_guard(s):
                return self.stmts(s.body, ctx)
            ctx["decisions"] += 1
            cc = self.cond(s.test, ctx)
            step = {"t": "if", "c": T.short(s.test, 120), "yes": self.stmts(s.body, ctx)}
            if cc:
                step["cc"] = cc
            if s.orelse:
                step["no"] = self.stmts(s.orelse, ctx)
            return [self.note(ctx, step)]
        if isinstance(s, (ast.For, ast.AsyncFor)):
            ctx["decisions"] += 1
            cc = self.cond(s.iter, ctx)
            step = {"t": "loop", "c": f"{T.short(s.target, 50)} in {T.short(s.iter, 70)}", "w": "each",
                    "body": self.stmts(s.body, ctx)}
            if cc:
                step["cc"] = cc
            out = [self.note(ctx, step)]
            if s.orelse:
                out.extend(self.stmts(s.orelse, ctx))
            return out
        if isinstance(s, ast.While):
            ctx["decisions"] += 1
            cc = self.cond(s.test, ctx)
            forever = isinstance(s.test, ast.Constant) and bool(s.test.value)
            step = {"t": "loop", "c": "" if forever else T.short(s.test, 100), "w": "while", "body": self.stmts(s.body, ctx)}
            if cc:
                step["cc"] = cc
            return [self.note(ctx, step)]
        if isinstance(s, ast.Try) or (hasattr(ast, "TryStar") and isinstance(s, getattr(ast, "TryStar"))):
            step = {"t": "try", "body": self.stmts(s.body, ctx) + self.stmts(s.orelse, ctx)}
            if s.handlers:
                ctx["decisions"] += len(s.handlers)
                if len(s.handlers) == 1:
                    h = s.handlers[0]
                    step["catch"] = {"v": self.handler_label(h, T), "body": self.stmts(h.body, ctx)}
                else:
                    cases = [{"c": self.handler_label(h, T) or "any other error", "body": self.stmts(h.body, ctx)} for h in s.handlers]
                    step["catch"] = {"v": "", "body": [self.note(ctx, {"t": "switch", "c": "the kind of error", "cases": cases})]}
            if s.finalbody:
                step["fin"] = self.stmts(s.finalbody, ctx)
            return [self.note(ctx, step)]
        if isinstance(s, (ast.With, ast.AsyncWith)):
            out = []
            for item in s.items:
                steps = self.expr(item.context_expr, ctx)
                if item.optional_vars is not None:
                    for st in steps:
                        if st.get("_n") is item.context_expr:
                            st["as"] = T.short(item.optional_vars, 50)
                out.extend(steps)
            out.extend(self.stmts(s.body, ctx))
            return out
        if hasattr(ast, "Match") and isinstance(s, getattr(ast, "Match")):
            ctx["decisions"] += len(s.cases)
            cases = []
            for c in s.cases:
                label = T.short(c.pattern, 60)
                if label == "_":
                    label = "anything else"
                if c.guard is not None:
                    label += f" if {T.short(c.guard, 40)}"
                cases.append({"c": label, "body": self.stmts(c.body, ctx)})
            return [*self.expr(s.subject, ctx), self.note(ctx, {"t": "switch", "c": T.short(s.subject, 80), "cases": cases})]
        if isinstance(s, ast.Return):
            steps = self.expr(s.value, ctx) if s.value is not None else []
            if s.value is None or (isinstance(s.value, ast.Constant) and s.value.value is None):
                return [*steps, self.note(ctx, {"t": "ret"})]
            return [*steps, self.note(ctx, {"t": "ret", "v": T.short(s.value, 120)})]
        if isinstance(s, ast.Raise):
            exc = s.exc
            if exc is not None and ("SystemExit" in T.short(exc, 40).split("(")[0]):
                ctx["effects"].append({"k": "exit", "pkg": "builtins", "fn": "SystemExit", "line": s.lineno})
                args = exc.args if isinstance(exc, ast.Call) else []
                return [self.note(ctx, {"t": "fx", "k": "exit", "pkg": "builtins", "fn": "SystemExit",
                                        "v": T.short(args[0], 110) if args else T.short(exc, 110)})]
            steps = self.expr(exc, ctx) if exc is not None else []
            return [*steps, self.note(ctx, {"t": "throw", "v": T.short(exc, 120) if exc is not None else "the same error again"})]
        if isinstance(s, ast.Assert):
            ctx["decisions"] += 1
            msg = T.short(s.msg, 100) if s.msg is not None else "AssertionError"
            return [*self.cond(s.test, ctx), self.note(ctx, {"t": "if", "c": T.short(s.test, 120), "unless": True,
                                                             "yes": [self.note(ctx, {"t": "throw", "v": msg})]})]
        if isinstance(s, ast.Break):
            return [self.note(ctx, {"t": "jump", "v": "break"})]
        if isinstance(s, ast.Continue):
            return [self.note(ctx, {"t": "jump", "v": "continue"})]
        if isinstance(s, ast.Delete):
            return []
        return self.expr(s, ctx)

    @staticmethod
    def handler_label(h, T):
        if h.type is None:
            return "any error"
        t = T.short(h.type, 60)
        return f"{t} as {h.name}" if h.name else t

    def env_name(self, call, ctx):
        """An env var read: os.environ.get("X"), os.getenv("X"), or the project's own reader helpers."""
        f = call.func
        if not call.args or not isinstance(call.args[0], ast.Constant) or not isinstance(call.args[0].value, str):
            return None
        name = call.args[0].value
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", name):
            return None
        text = ctx["mod"].text.short(f, 60)
        if re.search(r"(^|\.)(environ\.get|getenv)$", text):
            return name
        last = f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else ""
        if last in self.readers:
            return name
        return None

    def call_step(self, n, ctx):
        T = ctx["mod"].text
        f = n.func
        env = self.env_name(n, ctx)
        if env:
            ctx["env"].add(env)
        pre = self.expr(f.value, ctx) if isinstance(f, ast.Attribute) else ([] if isinstance(f, ast.Name) else self.expr(f, ctx))
        arg_steps = []
        cbs = []
        args = [(None, a) for a in n.args] + [(k.arg, k.value) for k in n.keywords]
        for kw, a in args:
            if isinstance(a, ast.Lambda):
                body = self.lambda_steps(a, ctx)
                if body:
                    cbs.append({"label": kw or f"{T.short(f, 40)}(…)", "body": body})
                continue
            if isinstance(a, (ast.Name, ast.Attribute)):
                r = self.resolve(a, ctx)
                if r and r[0] == "sym" and self.by_id.get(r[1], {}).get("_fn") is not None and r[1] != ctx["sym"]["id"]:
                    self.link(ctx, r[1], "use")
                    arg_steps.append(self.note(ctx, {"t": "use", "id": r[1], "v": kw or f"an argument to {T.short(f, 40)}"}))
                    continue
            if isinstance(a, ast.Starred):
                a = a.value
            arg_steps.extend(self.expr(a, ctx))
        target = self.resolve(f, ctx) if isinstance(f, (ast.Name, ast.Attribute)) else None
        v = T.short(n, 110)
        wait = {"await": True} if ctx["awaiting"] is n else {}
        step = None
        if target and target[0] == "sym":
            sym = self.by_id.get(target[1])
            self.link(ctx, target[1], "call")
            step = {"t": "call", "id": target[1], "v": v, **wait}
            if sym and sym["kind"] in ("class", "type"):
                step["new"] = True
                init = self.method_of(target[1], "__init__")
                if init:
                    self.link(ctx, init, "call")
        elif target and target[0] == "param":
            step = {"t": "call", "param": target[1], "v": v, **wait}
        elif target and target[0] in ("ext",):
            pkg, qual = target[1], target[2]
            fn = qual.split(".")[-1]
            k = effect_of(pkg, fn, qual, n, ctx["mod"].import_pkgs)
            if k:
                step = self.fx(ctx, k, pkg, fn, n, v, wait)
        elif target and target[0] == "unknown-attr" and isinstance(f, ast.Attribute):
            k, pkg = method_effect(f.attr, n, ctx["mod"].import_pkgs, T.short(f.value, 40))
            if k:
                step = self.fx(ctx, k, pkg, f.attr, n, v, wait, recv=f.value)
        if step is None:
            return [*pre, *arg_steps, *[self.note(ctx, {"t": "cb", **c}) for c in cbs]]
        step["_n"] = n
        if cbs:
            step["cbs"] = cbs
        return [*pre, *arg_steps, self.note(ctx, step)]

    def fx(self, ctx, k, pkg, fn, n, v, wait, recv=None):
        T = ctx["mod"].text
        on = None
        if k in ("file-read", "file-write") and recv is not None and fn in ("write_text", "write_bytes", "read_text", "read_bytes", "open", "unlink", "rmdir"):
            on = T.short(recv, 40)
        elif k in ("file-read", "file-write", "db-read", "db-write"):
            # json/pickle/joblib.dump(obj, file): the file is the second argument
            first = (n.args[1] if len(n.args) > 1 else None) if fn == "dump" else (n.args[0] if n.args else None)
            if first is None:
                for kw in n.keywords:
                    if kw.arg in ("path", "file", "filename", "fname", "path_or_buf", "filepath", "fp", "name"):
                        first = kw.value
            if first is not None:
                on = T.short(first, 40)
            elif recv is not None:
                on = T.short(recv, 40)
        step = {"t": "fx", "k": k, "pkg": pkg, "fn": fn, "v": v, **({"on": on} if on else {}), **wait}
        ctx["effects"].append({"k": k, "pkg": pkg, "fn": fn, **({"on": on} if on else {}), "line": n.lineno})
        return step

    def lambda_steps(self, lam, ctx):
        saved = ctx["scopes"]
        ctx["scopes"] = [{a.arg: ("param", a.arg, None) for a in lam.args.args}, *saved]
        out = self.expr(lam.body, ctx)
        ctx["scopes"] = saved
        return out

    def expr(self, n, ctx):
        if n is None or ctx["count"] > MAX_STEPS:
            return []
        T = ctx["mod"].text
        if isinstance(n, ast.Call):
            return self.call_step(n, ctx)
        if isinstance(n, ast.Await):
            was = ctx["awaiting"]
            ctx["awaiting"] = n.value
            out = self.expr(n.value, ctx)
            ctx["awaiting"] = was
            return out
        if isinstance(n, ast.Lambda):
            body = self.lambda_steps(n, ctx)
            return [self.note(ctx, {"t": "cb", "label": "an inline function", "body": body})] if body else []
        if isinstance(n, ast.IfExp):
            c = self.expr(n.test, ctx)
            a = self.expr(n.body, ctx)
            b = self.expr(n.orelse, ctx)
            if ctx["cond"]:
                return [*c, *a, *b]
            if not a and not b:
                return c
            ctx["decisions"] += 1
            step = {"t": "if", "c": T.short(n.test, 120), "x": True, "yes": a}
            if b:
                step["no"] = b
            return [*c, self.note(ctx, step)]
        if isinstance(n, ast.BoolOp):
            out = self.expr(n.values[0], ctx)
            for prev, val in zip(n.values, n.values[1:]):
                r = self.expr(val, ctx)
                if not r:
                    continue
                ctx["decisions"] += 1
                if ctx["cond"]:
                    out.extend(r)
                    continue
                step = {"t": "if", "c": T.short(prev, 120), "x": True, "yes": r}
                if isinstance(n.op, ast.Or):
                    step["unless"] = True
                out.append(self.note(ctx, step))
            return out
        if isinstance(n, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
            saved = ctx["scopes"]
            local = {}
            for g in n.generators:
                for t in ast.walk(g.target):
                    if isinstance(t, ast.Name):
                        local[t.id] = ("local", t.id, None)
            ctx["scopes"] = [local, *saved]
            iters = []
            for g in n.generators:
                iters.extend(self.expr(g.iter, ctx))
            body = []
            for g in n.generators:
                for cond in g.ifs:
                    body.extend(self.cond(cond, ctx))
            if isinstance(n, ast.DictComp):
                body.extend(self.expr(n.key, ctx))
                body.extend(self.expr(n.value, ctx))
            else:
                body.extend(self.expr(n.elt, ctx))
            ctx["scopes"] = saved
            if not body:
                return iters
            g = n.generators[0]
            ctx["decisions"] += 1
            return [*iters, self.note(ctx, {"t": "loop", "w": "each", "c": f"{T.short(g.target, 40)} in {T.short(g.iter, 60)}", "body": body})]
        if isinstance(n, (ast.Yield, ast.YieldFrom)):
            steps = self.expr(n.value, ctx) if n.value is not None else []
            return [*steps, self.note(ctx, {"t": "ret", "gen": True, **({"v": T.short(n.value, 120)} if n.value is not None else {})})]
        if isinstance(n, ast.NamedExpr):
            steps = self.expr(n.value, ctx)
            for st in steps:
                if st.get("_n") is n.value:
                    st["as"] = T.short(n.target, 40)
            return steps
        if isinstance(n, ast.Subscript):
            text = T.short(n.value, 40)
            if re.search(r"(^|\.)environ$", text) and isinstance(n.ctx, ast.Load):
                sl = slice_of(n)
                if isinstance(sl, ast.Constant) and isinstance(sl.value, str) and re.fullmatch(r"[A-Z][A-Z0-9_]*", sl.value):
                    ctx["env"].add(sl.value)
            return [*self.expr(n.value, ctx), *self.expr(n.slice, ctx)]
        if isinstance(n, ast.Name):
            if isinstance(n.ctx, ast.Load):
                r = self.resolve(n, ctx)
                if r and r[0] == "sym" and r[1] != ctx["sym"]["id"] and self.by_id.get(r[1], {}).get("_fn") is not None:
                    self.link(ctx, r[1], "use")
            return []
        if isinstance(n, ast.Attribute):
            if isinstance(n.ctx, ast.Load) and isinstance(n.value, ast.Name):
                r = self.resolve(n, ctx)
                if r and r[0] == "sym" and r[1] != ctx["sym"]["id"] and self.by_id.get(r[1], {}).get("_fn") is not None:
                    self.link(ctx, r[1], "use")
            return self.expr(n.value, ctx)
        out = []
        for c in ast.iter_child_nodes(n):
            if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            out.extend(self.expr(c, ctx))
        return out

    @staticmethod
    def clean(steps):
        out = []
        for s in steps:
            s = {k: v for k, v in s.items() if k != "_n"}
            for k in ("yes", "no", "body", "kids", "cc", "fin"):
                if isinstance(s.get(k), list):
                    s[k] = Scanner.clean(s[k])
            if s.get("catch"):
                s["catch"] = {**s["catch"], "body": Scanner.clean(s["catch"]["body"])}
            if s.get("cases"):
                s["cases"] = [{**c, "body": Scanner.clean(c["body"])} for c in s["cases"]]
            if s.get("cbs"):
                s["cbs"] = [{**c, "body": Scanner.clean(c["body"])} for c in s["cbs"]]
            out.append(s)
        return out

    # ---------------------------------------------------------------- signatures
    def params_of(self, sym, fn):
        m = sym["_mod"]
        T = m.text
        a = fn.args
        positional = [*getattr(a, "posonlyargs", []), *a.args]
        defaults = [None] * (len(positional) - len(a.defaults)) + list(a.defaults)
        dparams = sym.get("_dparams") or {}
        out = []
        skip_first = sym["kind"] == "method" and not any(
            isinstance(d, ast.Name) and d.id == "staticmethod" for d in getattr(fn, "decorator_list", []))

        def one(arg, default, rest=False, kw=False):
            p = {"name": arg.arg}
            if rest:
                p["rest"] = True
            if default is not None:
                p["opt"] = True
                p["def"] = T.short(default, 60)
            if arg.annotation is not None:
                p["type"] = T.short(arg.annotation, 160)
                refs = self.type_refs(arg.annotation, m)
                if refs:
                    p["refs"] = refs
            elif default is not None and isinstance(default, ast.Constant):
                p["type"] = type(default.value).__name__ if default.value is not None else "None"
            elif rest:
                p["type"] = "keyword arguments" if kw else "more arguments"
            else:
                p["type"] = ""
            if dparams.get(arg.arg):
                p["doc"] = dparams[arg.arg]
            return p

        for i, (arg, d) in enumerate(zip(positional, defaults)):
            if i == 0 and skip_first:
                continue
            out.append(one(arg, d))
        if a.vararg:
            out.append(one(a.vararg, None, rest=True))
        for arg, d in zip(a.kwonlyargs, a.kw_defaults):
            out.append(one(arg, d))
        if a.kwarg:
            out.append(one(a.kwarg, None, rest=True, kw=True))
        return out

    def type_refs(self, ann, m):
        refs = []
        for n in ast.walk(ann):
            if isinstance(n, (ast.Name, ast.Attribute)):
                r = self.resolve_static(n, m)
                if r and r[0] == "sym" and self.by_id.get(r[1], {}).get("kind") in ("type", "class") and r[1] not in refs:
                    refs.append(r[1])
        return refs

    def returns_of(self, sym, fn):
        m = sym["_mod"]
        if isinstance(fn, ast.Lambda):
            return {}
        if fn.returns is not None:
            out = {"returns": m.text.short(fn.returns, 200), "declaredReturn": True}
            refs = self.type_refs(fn.returns, m)
            if refs:
                out["retRefs"] = refs
            return out
        if sym["name"] == "__init__":
            return {}
        has_yield = has_value = False
        for n in self.walk_expr_nodes(fn.body):
            if isinstance(n, (ast.Yield, ast.YieldFrom)):
                has_yield = True
            if isinstance(n, ast.Return) and n.value is not None and not (isinstance(n.value, ast.Constant) and n.value.value is None):
                has_value = True
        if has_yield:
            return {"returns": "a generator (hands out values one at a time)"}
        if not has_value:
            return {"returns": "None"}
        return {}

    # ---------------------------------------------------------------- entry points
    def entry_decorator(self, d, m):
        """A decorator that makes the function start on its own: a web route, a schedule, a command."""
        return self.decorator_entry(d, m, "x") is not None

    def decorator_entry(self, d, m, name):
        T = m.text
        call = d if isinstance(d, ast.Call) else None
        f = call.func if call else d
        attr = f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else ""
        first = call.args[0] if call and call.args else None
        kws = {k.arg: k.value for k in call.keywords} if call else {}

        def lit(v):
            """A literal, or a module-level constant it names (`label=FEED_LABEL`)."""
            if isinstance(v, ast.Constant):
                return v.value
            if isinstance(v, ast.Name):
                for st in m.tree.body:
                    if isinstance(st, ast.Assign) and any(isinstance(t, ast.Name) and t.id == v.id for t in st.targets) \
                            and isinstance(st.value, ast.Constant):
                        return st.value.value
            return None
        if attr in HTTP_VERBS | {"route", "websocket", "api_route"} and first is not None and isinstance(lit(first), str) and lit(first).startswith("/"):
            methods = "GET"
            if attr in HTTP_VERBS:
                methods = attr.upper()
            elif "methods" in kws and isinstance(kws["methods"], (ast.List, ast.Tuple)):
                methods = "/".join(str(lit(e)) for e in kws["methods"].elts if lit(e))
            elif attr == "websocket":
                methods = "WEBSOCKET"
            return ("endpoint", f"{methods} {lit(first)}")
        if "modal" in m.import_pkgs:
            if attr == "function" and "schedule" in kws:
                sched = kws["schedule"]
                text = T.short(sched, 80)
                cron = re.search(r"Cron\(\s*['\"]([^'\"]+)['\"]", text)
                tz = re.search(r"timezone\s*=\s*['\"]([^'\"]+)['\"]", text)
                if cron:
                    return ("task", f"on a schedule: cron {cron.group(1)}{f' ({tz.group(1)})' if tz else ''}")
                return ("task", f"on a schedule: {text}")
            if attr in ("fastapi_endpoint", "web_endpoint"):
                method = lit(kws.get("method")) or "GET"
                label = lit(kws.get("label"))
                return ("endpoint", f"{method} web link{f' ({label})' if label else ''}")
            if attr in ("asgi_app", "wsgi_app"):
                return ("endpoint", "a web app served by Modal")
            if attr == "local_entrypoint":
                return ("command", f"modal run {m.file}::{name}")
        if m.import_pkgs & {"click", "typer"} and attr == "command":
            cmd = lit(first) if first is not None else None
            return ("command", f"the {cmd or name.replace('_', '-')} command")
        if m.import_pkgs & {"celery"} and attr in ("task", "shared_task"):
            return ("task", f"background task {name}")
        if m.import_pkgs & {"apscheduler", "schedule"} and attr in ("scheduled_job", "do"):
            return ("task", f"on a schedule: {T.short(d, 60)}")
        return None

    def usage_lines(self, m):
        doc = ast.get_docstring(m.tree) or ""
        base = m.file.split("/")[-1]
        out = []
        for line in doc.split("\n"):
            s = line.strip()
            if base not in s or not re.search(r"\b(python3?|py|streamlit run|uv run|poetry run)\b", s):
                continue
            s = re.sub(r"^(\$|>|>>>)\s+", "", s)
            s = re.sub(r"^(run|usage|example|e\.g\.)s?\s*:\s*", "", s, flags=re.I)
            s = re.split(r"\s{2,}#|\s#\s", s)[0].strip()
            s = squash(s)
            if s and s not in out:
                out.append(s)
        return out[:4]

    def entries_for(self):
        importers = {}
        for m in self.mods:
            for f in m.imports_int:
                importers.setdefault(f, set()).add(m.file)
        for s in self.symbols:
            if s.get("_fn") is None or s.get("parent") and s["kind"] != "method":
                continue
            node = s["_fn"]
            for d in getattr(node, "decorator_list", []):
                e = self.decorator_entry(d, s["_mod"], s["name"])
                if e:
                    if s["kind"] in ("function", "method"):
                        s["kind"] = e[0]
                    self.entries.setdefault(s["id"], {"id": s["id"], "file": s["file"], "kind": e[0], "list": []})["list"].append(e[1])
        for s in self.symbols:
            if s["name"] != "(top level)":
                continue
            m = s["_mod"]
            imported = bool(importers.get(m.file))
            streamlit = "streamlit" in m.import_pkgs and any(e["k"] in ("screen", "exit") and e["pkg"] == "streamlit" for e in s.get("_effects", []))
            has_main = any(Scanner.is_main_guard(st) for st in m.tree.body)
            # A file whose functions start on their own (routes, schedules, commands) is loaded by its framework.
            framework = any(e["file"] == m.file for e in self.entries.values())
            if streamlit and not imported:
                s["kind"] = "page"
                trig = [u for u in self.usage_lines(m) if "streamlit" in u] or [f"streamlit run {m.file}"]
            elif has_main or (m.program and not imported and not framework):
                s["kind"] = "script"
                trig = self.usage_lines(m) or [f"python {m.file}"]
            else:
                s["kind"] = "module"
                continue
            self.entries.setdefault(s["id"], {"id": s["id"], "file": s["file"], "kind": s["kind"], "list": []})["list"].extend(trig)

    # ---------------------------------------------------------------- tests
    def scan_tests(self):
        for m in self.mods:
            if not m.is_test:
                continue
            for st in m.tree.body:
                fns = []
                if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef)) and st.name.startswith("test"):
                    fns.append(st)
                elif isinstance(st, ast.ClassDef) and st.name.startswith("Test"):
                    fns += [x for x in st.body if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef)) and x.name.startswith("test")]
                for fn in fns:
                    title = re.sub(r"^test_?", "", fn.name).replace("_", " ").strip() or fn.name
                    for n in ast.walk(fn):
                        if isinstance(n, (ast.Name, ast.Attribute)) and isinstance(getattr(n, "ctx", None), ast.Load):
                            r = self.resolve_static(n, m)
                            if r and r[0] == "sym":
                                lst = self.tests.setdefault(r[1], [])
                                if not any(t["file"] == m.file and t["title"] == title for t in lst):
                                    lst.append({"file": m.file, "title": title})

    # ---------------------------------------------------------------- run
    def run(self):
        self.load()
        self.declare()
        self.collect()
        # class bases and value types, now every symbol exists
        for s in self.symbols:
            if s.get("_bases_nodes"):
                bases = []
                for b in s["_bases_nodes"]:
                    r = self.resolve_static(b, s["_mod"])
                    if r and r[0] == "sym":
                        bases.append(r[1])
                s["_bases"] = bases
            if s.get("_value") is not None:
                t = self.type_of_value(s["_value"], s["_mod"])
                if t:
                    s["_vtype"] = t
        # module top levels
        for m in self.mods:
            if m.is_test:
                continue
            top = []
            for st in m.tree.body:
                if isinstance(st, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    continue
                if isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant):
                    continue
                if not m.program and isinstance(st, (ast.Assign, ast.AnnAssign)):
                    continue
                if Scanner.is_setup_only(st):
                    continue
                top.append(st)
            if top:
                doc, _ = clean_doc(ast.get_docstring(m.tree) or "")
                sym = {"id": f"{m.file}#(top level)", "name": "(top level)", "file": m.file, "kind": "module", "doc": doc}
                sym["line"] = top[0].lineno
                sym["end"] = getattr(top[-1], "end_lineno", top[-1].lineno)
                sym["_top"] = top
                sym["_mod"] = m
                sym["_fn"] = None
                self.symbols.append(sym)
                self.by_id[sym["id"]] = sym
        # outlines
        for s in self.symbols:
            m = s["_mod"]
            ctx = {"sym": s, "mod": m, "count": 0, "decisions": 0, "links": {}, "effects": [], "env": set(),
                   "cond": False, "awaiting": None, "scopes": []}
            outline = []
            fn = s.get("_fn")
            if fn is not None:
                ctx["scopes"] = self.scope_for(s)
                if isinstance(fn, ast.Lambda):
                    outline = [*self.expr(fn.body, ctx), self.note(ctx, {"t": "ret", "v": m.text.short(fn.body, 120)})]
                else:
                    outline = self.stmts(fn.body, ctx)
                    # decorators that are ours
                    for d in fn.decorator_list:
                        target = d.func if isinstance(d, ast.Call) else d
                        if isinstance(target, (ast.Name, ast.Attribute)):
                            r = self.resolve(target, {**ctx, "scopes": []})
                            if r and r[0] == "sym":
                                self.link(ctx, r[1], "use")
                s["params"] = self.params_of(s, fn)
                s.update(self.returns_of(s, fn))
            elif s.get("_top"):
                outline = self.stmts(s["_top"], ctx)
            elif s.get("_value") is not None:
                outline = self.expr(s["_value"], ctx)
            elif s["kind"] in ("class", "type"):
                node = s["_node"]
                for st in node.body:
                    if isinstance(st, (ast.Assign, ast.AnnAssign)) and getattr(st, "value", None) is not None:
                        outline.extend(self.expr(st.value, ctx))
            s["_effects"] = ctx["effects"]
            s["outline"] = self.clean(outline)
            s["links"] = [{"id": i, "how": h} for i, h in sorted(ctx["links"].items())]
            s["effects"] = ctx["effects"]
            s["env"] = sorted(ctx["env"])
            s["decisions"] = ctx["decisions"]
        self.entries_for()
        self.scan_tests()
        # imports, for the Code tab's import graph
        for m in self.mods:
            self.imports[m.file] = {"internal": sorted(f for f in m.imports_int if f != m.file),
                                    "external": sorted(m.imports_ext)}
        out = []
        for s in self.symbols:
            if s["name"] == "(top level)" and not s["outline"] and s["id"] not in self.entries:
                continue
            r = {k: v for k, v in s.items() if not k.startswith("_")}
            for k in ("doc", "exported", "async", "outline", "links", "effects", "env", "decisions"):
                if not r.get(k):
                    r.pop(k, None)
            out.append(r)
        out.sort(key=lambda r: (r["file"], r["line"], r["id"]))
        entries = sorted(({"id": e["id"], "file": e["file"], "kind": e["kind"], "trigger": "; ".join(dict.fromkeys(e["list"]))}
                          for e in self.entries.values()), key=lambda e: (e["kind"], e["trigger"]))
        tests = {k: sorted(v, key=lambda t: (t["file"], t["title"])) for k, v in self.tests.items()}
        return {"symbols": out, "entries": entries, "wiring": [], "tests": tests, "sources": self.sources,
                "imports": self.imports, "warnings": self.warnings,
                "files": len([m for m in self.mods if not m.is_test])}


def main():
    req = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    res = Scanner(req).run()
    sys.stdout.buffer.write(json.dumps(res, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


if __name__ == "__main__":
    main()

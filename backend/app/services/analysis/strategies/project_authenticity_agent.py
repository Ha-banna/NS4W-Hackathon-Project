from __future__ import annotations

import hashlib
import io
import json
import os
import random
import re
import time
import zipfile
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, TypedDict

import numpy as np
import requests
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

load_dotenv()

MAX_REPOS_TOTAL = 200
MAX_REPOS_DEEP = 15
TOP_DEEP_SNIPPETS = 10

MAX_ZIP_BYTES_PER_REPO = 6_000_000
MAX_FILES_PER_REPO = 140
MAX_FILE_BYTES = 900_000
MAX_TOTAL_CHUNKS = 6500

CHUNK_MAX_LINES = 140
CHUNK_OVERLAP = 25

LLM_MODEL = "gpt-4.1-mini"
EMBED_MODEL = "text-embedding-3-small"
LLM_TIMEOUT = 80

CACHE_DIR = ".cache/github_zip"
CACHE_TTL_SECONDS = 24 * 3600

PENALIZE_FORKS = True

HTTP_RETRIES = 3
HTTP_BACKOFF = 0.7


class Evidence(TypedDict, total=False):
    repo: str
    file: str
    lines: str
    excerpt: str
    reasoning: str


class RepoAuthenticity(TypedDict, total=False):
    scan_mode: str                    # "deep" | "shallow"
    authenticity_score: float         # 0..100 (higher = more likely original)
    labels: List[str]                 # original | tutorial_clone | copy_paste | ai_generated | template_based | unclear
    confidence: float                 # 0..1
    signals: Dict[str, Any]           # numeric+meta signals
    evidence: List[Evidence]          # verified, only for deep repos
    notes: str


class GraphState(TypedDict, total=False):
    cv_json: Dict[str, Any]
    github_user: Optional[str]

    referenced_repos: List[str]       # normalized repo keys: "user/repo" (lower)
    repos_all: List[Dict[str, Any]]   # every repo we discovered (metadata)
    repos_deep: List[Dict[str, Any]]  # subset for deep scan (metadata)

    chunks: List[Dict[str, Any]]      # {"id","repo","file","start_line","end_line","text"}
    chunk_vectors: Any                # np.ndarray (N,D)
    repo_slices: Dict[str, Tuple[int, int]]  # repo_full -> [start,end)

    signals_by_repo: Dict[str, Dict[str, Any]]
    decisions_by_repo: Dict[str, RepoAuthenticity]

    meta: Dict[str, Any]
    final_output: Dict[str, Any]


def find_all_strings(obj: Any, limit: int = 30000) -> List[str]:
    out: List[str] = []

    def rec(x: Any):
        if len(out) >= limit:
            return
        if isinstance(x, str):
            out.append(x)
        elif isinstance(x, dict):
            for v in x.values():
                rec(v)
        elif isinstance(x, list):
            for v in x:
                rec(v)

    rec(obj)
    return out


_REPO_URL_RE = re.compile(
    r"(?:https?://)?(?:www\.)?github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)",
    flags=re.IGNORECASE,
)

_RAW_REPO_URL_RE = re.compile(
    r"(?:https?://)?raw\.githubusercontent\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/",
    flags=re.IGNORECASE,
)

_REPO_SLUG_RE = re.compile(r"\b([A-Za-z0-9_.-]{1,39})/([A-Za-z0-9_.-]+)\b")


def normalize_repo_full_name(x: str) -> Optional[str]:
    """
    Normalize any repo reference to canonical key: "user/repo" (lowercase).
    Handles:
      - github.com/user/repo[/...]
      - raw.githubusercontent.com/user/repo/...
      - "user/repo"
      - strips .git, querystrings, fragments, trailing punctuation
    """
    if not x:
        return None

    s = x.strip()
    s = s.strip(" \t\r\n\"'()[]{}<>,.;:")
    s = s.replace("\\", "/")

    m = _RAW_REPO_URL_RE.search(s)
    if m:
        user, repo = m.group(1), m.group(2)
        repo = repo.split("?")[0].split("#")[0]
        if repo.endswith(".git"):
            repo = repo[:-4]
        return f"{user}/{repo}".lower()

    m = _REPO_URL_RE.search(s)
    if m:
        user, repo = m.group(1), m.group(2)
        repo = repo.split("?")[0].split("#")[0]
        repo = repo.split("/")[0]
        repo = repo.rstrip(".")
        if repo.endswith(".git"):
            repo = repo[:-4]
        user = user.strip(" \t\r\n\"'()[]{}<>,.;:")
        repo = repo.strip(" \t\r\n\"'()[]{}<>,.;:")
        if not user or not repo:
            return None
        return f"{user}/{repo}".lower()

    if "/" in s:
        parts = s.split("/")
        if len(parts) >= 2:
            user, repo = parts[0], parts[1]
            repo = repo.split("?")[0].split("#")[0]
            repo = repo.rstrip(".")
            if repo.endswith(".git"):
                repo = repo[:-4]
            user = user.strip(" \t\r\n\"'()[]{}<>,.;:")
            repo = repo.strip(" \t\r\n\"'()[]{}<>,.;:")
            if not user or not repo:
                return None
            return f"{user}/{repo}".lower()

    return None


def extract_github_username(cv: Dict[str, Any]) -> Optional[str]:
    for s in find_all_strings(cv):
        if "github" not in s.lower():
            continue
        m = re.search(r"github\.com/([^/\s\)\]]+)", s, flags=re.IGNORECASE)
        if m:
            return m.group(1)
    return None


def extract_referenced_repos(cv: Dict[str, Any]) -> List[str]:
    """
    Extract repos referenced in CV JSON.
    Returns normalized canonical keys: "user/repo" lowercased.
    Handles:
      - https://github.com/user/repo
      - https://github.com/user/repo/tree/main/...
      - markdown links, trailing punctuation, query strings, .git
      - raw.githubusercontent.com/user/repo/...
      - plain "user/repo" only when it appears in repo-ish context
    """
    found: List[str] = []
    strings = find_all_strings(cv)

    for s in strings:
        low = s.lower()
        if "github" not in low:
            continue

        for m in _REPO_URL_RE.finditer(s):
            norm = normalize_repo_full_name(f"{m.group(1)}/{m.group(2)}")
            if norm:
                found.append(norm)

        for m in _RAW_REPO_URL_RE.finditer(s):
            norm = normalize_repo_full_name(f"{m.group(1)}/{m.group(2)}")
            if norm:
                found.append(norm)

    ctx_words = ("repo", "repository", "github", "project", "source", "code", "link")
    for s in strings:
        low = s.lower()
        if not any(w in low for w in ctx_words):
            continue

        for m in _REPO_SLUG_RE.finditer(s):
            norm = normalize_repo_full_name(f"{m.group(1)}/{m.group(2)}")
            if norm:
                found.append(norm)

    seen = set()
    out = []
    for x in found:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


@dataclass
class GitHubPublic:
    user_agent: str = "public-cv-authenticity-agent/1.1"

    def _request(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: Tuple[int, int] = (10, 45),
    ) -> requests.Response:
        backoff = HTTP_BACKOFF
        last_exc: Optional[Exception] = None
        for _attempt in range(HTTP_RETRIES):
            try:
                r = requests.get(
                    url,
                    params=params,
                    headers={"User-Agent": self.user_agent, "Accept": "application/vnd.github+json"},
                    timeout=timeout,
                    allow_redirects=True,
                )
                return r
            except Exception as e:
                last_exc = e
                time.sleep(backoff + random.random() * 0.2)
                backoff *= 2
        raise RuntimeError(f"HTTP request failed after retries: {url}. Last error: {last_exc}")

    def list_repos_all(self, user: str, max_repos: int = MAX_REPOS_TOTAL) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        meta: Dict[str, Any] = {"pages_fetched": 0, "rate_limited": False}

        page = 1
        per_page = 100

        while True:
            url = f"https://api.github.com/users/{user}/repos"
            r = self._request(url, params={"per_page": per_page, "page": page, "sort": "pushed"}, timeout=(10, 30))

            if r.status_code in (403, 429):
                meta["rate_limited"] = True
                break
            if r.status_code != 200:
                break

            data = r.json()
            if not isinstance(data, list) or not data:
                break

            out.extend(data)
            meta["pages_fetched"] += 1

            if len(out) >= max_repos or len(data) < per_page:
                break
            page += 1

        out = sorted(out, key=lambda x: x.get("pushed_at") or "", reverse=True)
        return out[:max_repos], meta

    def get_repo(self, full_name: str) -> Optional[Dict[str, Any]]:
        url = f"https://api.github.com/repos/{full_name}"
        try:
            r = self._request(url, timeout=(10, 30))
            if r.status_code != 200:
                return None
            return r.json()
        except Exception:
            return None

    def download_zipball(self, full_name: str, default_branch: str) -> bytes:
        url = f"https://api.github.com/repos/{full_name}/zipball/{default_branch}"
        r = self._request(url, timeout=(10, 90))
        if r.status_code != 200:
            raise RuntimeError(f"zipball download failed {full_name}@{default_branch}: {r.status_code}")
        return r.content


def _ensure_dir(p: str) -> None:
    os.makedirs(p, exist_ok=True)


def cache_key(full_name: str, branch: str) -> str:
    h = hashlib.sha256(f"{full_name}@{branch}".encode("utf-8")).hexdigest()[:16]
    safe = full_name.replace("/", "__")
    return f"{safe}__{branch}__{h}.zip"


def cache_get(full_name: str, branch: str) -> Optional[bytes]:
    _ensure_dir(CACHE_DIR)
    fp = os.path.join(CACHE_DIR, cache_key(full_name, branch))
    if not os.path.exists(fp):
        return None
    age = time.time() - os.path.getmtime(fp)
    if age > CACHE_TTL_SECONDS:
        return None
    try:
        with open(fp, "rb") as f:
            return f.read()
    except Exception:
        return None


def cache_set(full_name: str, branch: str, data: bytes) -> None:
    _ensure_dir(CACHE_DIR)
    fp = os.path.join(CACHE_DIR, cache_key(full_name, branch))
    try:
        with open(fp, "wb") as f:
            f.write(data)
    except Exception:
        pass


ALLOWED_EXTS = {
    ".py", ".ipynb", ".js", ".ts", ".tsx", ".jsx",
    ".java", ".cpp", ".c", ".h", ".hpp",
    ".go", ".rs", ".cs",
    ".sql",
    ".md", ".toml", ".yml", ".yaml", ".json",
}

SKIP_DIRS = ("/.git/", "/node_modules/", "/.venv/", "/venv/", "/dist/", "/build/", "/__pycache__/")

def should_keep(path: str) -> bool:
    p = path.replace("\\", "/")
    if any(d in p for d in SKIP_DIRS):
        return False
    ext = os.path.splitext(p)[1].lower()
    return ext in ALLOWED_EXTS


def extract_text_from_ipynb(raw: str) -> str:
    try:
        j = json.loads(raw)
        cells = j.get("cells", [])
        parts = []
        for c in cells:
            src = c.get("source", [])
            if isinstance(src, list):
                parts.append("".join(src))
            elif isinstance(src, str):
                parts.append(src)
        return "\n\n".join(parts)
    except Exception:
        return raw


def chunk_text_lines(text: str, max_lines: int = CHUNK_MAX_LINES, overlap: int = CHUNK_OVERLAP) -> List[Tuple[int, int, str]]:
    lines = text.splitlines()
    out = []
    i = 0
    n = len(lines)
    while i < n:
        j = min(n, i + max_lines)
        chunk = "\n".join(lines[i:j])
        out.append((i + 1, j, chunk))
        if j == n:
            break
        i = max(0, j - overlap)
    return out


def build_chunks_from_zip(zip_bytes: bytes, repo_full: str, meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    chunks: List[Dict[str, Any]] = []
    try:
        z = zipfile.ZipFile(io.BytesIO(zip_bytes))
    except Exception:
        meta["zip_parse_failures"] = meta.get("zip_parse_failures", 0) + 1
        return chunks

    total_bytes = 0
    files_seen = 0
    local_chunk_id = 0

    for info in z.infolist():
        if info.is_dir():
            continue
        if files_seen >= MAX_FILES_PER_REPO:
            break
        if info.file_size > MAX_FILE_BYTES:
            continue

        path = info.filename
        path = "/".join(path.split("/")[1:])  
        if not path or not should_keep(path):
            continue

        raw = z.read(info)
        total_bytes += len(raw)
        if total_bytes > MAX_ZIP_BYTES_PER_REPO:
            break

        try:
            text = raw.decode("utf-8", errors="ignore")
        except Exception:
            continue

        if path.lower().endswith(".ipynb"):
            text = extract_text_from_ipynb(text)

        for (s, e, ch) in chunk_text_lines(text):
            if not ch.strip():
                continue
            chunks.append({
                "id": f"{repo_full}:{path}:{s}-{e}:{local_chunk_id}",
                "repo": repo_full,
                "file": path,
                "start_line": s,
                "end_line": e,
                "text": ch,
            })
            local_chunk_id += 1
            if len(chunks) >= MAX_TOTAL_CHUNKS:
                return chunks

        files_seen += 1

    return chunks


def simhash64(text: str) -> int:
    tokens = re.findall(r"[A-Za-z_]\w{2,}", text)
    if not tokens:
        return 0
    v = [0] * 64
    for t in tokens[:1200]:
        h = int(hashlib.md5(t.encode("utf-8")).hexdigest(), 16)
        for i in range(64):
            bit = (h >> i) & 1
            v[i] += 1 if bit else -1
    out = 0
    for i in range(64):
        if v[i] > 0:
            out |= (1 << i)
    return out


def chunk_is_boilerplate(text: str) -> float:
    low = text.lower()
    score = 0.0
    if "eslint" in low or "prettier" in low or "tsconfig" in low:
        score += 0.25
    if "docker" in low or "compose" in low:
        score += 0.15
    punct = sum(ch in "{}[]:,\"" for ch in text)
    score += min(0.25, punct / max(1, len(text)) * 20)
    if len(text) < 350:
        score += 0.1
    return max(0.0, min(1.0, score))


def quick_shallow_score(repo_meta: Dict[str, Any]) -> Tuple[float, List[str], float, str]:
    is_fork = bool(repo_meta.get("fork"))
    size_kb = int(repo_meta.get("size") or 0)
    desc = (repo_meta.get("description") or "").lower()
    name = (repo_meta.get("name") or "").lower()
    has_wiki = bool(repo_meta.get("has_wiki"))
    has_pages = bool(repo_meta.get("has_pages"))
    stars = int(repo_meta.get("stargazers_count") or 0)

    labels = ["unclear"]
    conf = 0.15
    score = 50.0
    notes = "Shallow scan (metadata only)."

    if is_fork:
        labels = ["template_based"]
        conf = 0.35
        score = 35.0
        notes = "Repo is a fork (often derived from others)."

    tutorial_words = ("tutorial", "course", "bootcamp", "practice", "lab", "assignment", "homework")
    if any(w in name for w in tutorial_words) or any(w in desc for w in tutorial_words):
        labels = ["tutorial_clone"]
        conf = max(conf, 0.35)
        score = min(score, 40.0)
        notes = "Repo name/description suggests tutorial/course material (shallow hint)."

    if size_kb <= 25:
        score = min(score, 35.0)
        conf = max(conf, 0.25)
        notes = "Repo is very small (shallow hint)."

    if stars >= 5 or has_pages or has_wiki:
        score = max(score, 55.0)
        conf = max(conf, 0.2)

    return float(max(0.0, min(100.0, score))), labels, float(max(0.0, min(1.0, conf))), notes


def embed_texts(emb: OpenAIEmbeddings, texts: List[str], batch: int = 64) -> np.ndarray:
    vecs: List[List[float]] = []
    for i in range(0, len(texts), batch):
        part = texts[i:i+batch]
        vecs.extend(emb.embed_documents(part))
    return np.asarray(vecs, dtype=np.float32)


def embed_query(emb: OpenAIEmbeddings, q: str) -> np.ndarray:
    v = emb.embed_query(q)
    return np.asarray(v, dtype=np.float32)


def cosine_topk(M: np.ndarray, q: np.ndarray, k: int) -> np.ndarray:
    qn = np.linalg.norm(q) + 1e-9
    Mn = np.linalg.norm(M, axis=1) + 1e-9
    sims = (M @ q) / (Mn * qn)
    k = min(k, len(sims))
    idx = np.argpartition(-sims, k-1)[:k]
    idx = idx[np.argsort(-sims[idx])]
    return idx


def _safe_json_parse(s: str) -> Optional[dict]:
    try:
        return json.loads(s)
    except Exception:
        m = re.search(r"\{.*\}", s, flags=re.S)
        if not m:
            return None
        try:
            return json.loads(m.group(0))
        except Exception:
            return None


def verify_evidence(items: List[Evidence], ctx_lookup: Dict[str, str]) -> List[Evidence]:
    verified: List[Evidence] = []
    for it in items:
        repo = (it.get("repo") or "").strip()
        file = (it.get("file") or "").strip()
        lines = (it.get("lines") or "").strip()
        excerpt = (it.get("excerpt") or "").strip()
        if not repo or not file or not lines or not excerpt:
            continue
        key = f"{repo}|{file}|{lines}"
        txt = ctx_lookup.get(key)
        if not txt:
            continue
        if excerpt not in txt:
            continue
        it["excerpt"] = excerpt[:220]
        it["reasoning"] = (it.get("reasoning") or "")[:260]
        verified.append(it)
    return verified


def llm_judge_repo(
    llm: ChatOpenAI,
    repo_full: str,
    repo_meta: Dict[str, Any],
    signals: Dict[str, Any],
    contexts: List[Dict[str, Any]],
) -> RepoAuthenticity:
    ctx_payload = []
    ctx_lookup: Dict[str, str] = {}

    for c in contexts:
        lines = f"L{c['start_line']}-L{c['end_line']}"
        snippet = c["text"]
        if len(snippet) > 1800:
            snippet = snippet[:1800] + "\n…"
        key = f"{repo_full}|{c['file']}|{lines}"
        ctx_payload.append({
            "repo": repo_full,
            "file": c["file"],
            "lines": lines,
            "snippet": snippet,
        })
        ctx_lookup[key] = c["text"]

    system = (
        "You are a conservative code authenticity evaluator for public portfolio projects.\n"
        "Estimate likelihood the project is original vs tutorial clone / copy-paste / AI-generated.\n"
        "Do NOT make absolute accusations; speak in likelihood terms.\n"
        "You MUST cite evidence only from provided snippets. Excerpts must be copied verbatim.\n"
        "Return JSON only."
    )

    user = {
        "repo": repo_full,
        "repo_meta": {
            "is_fork": bool(repo_meta.get("fork")),
            "created_at": repo_meta.get("created_at"),
            "pushed_at": repo_meta.get("pushed_at"),
            "language": repo_meta.get("language"),
            "size_kb": repo_meta.get("size"),
            "stargazers": repo_meta.get("stargazers_count"),
            "forks": repo_meta.get("forks_count"),
            "description": repo_meta.get("description"),
            "homepage": repo_meta.get("homepage"),
        },
        "signals": signals,
        "snippets": ctx_payload,
        "output_schema": {
            "authenticity_score": "0..100 (higher = more likely original work)",
            "labels": "list among: original, tutorial_clone, copy_paste, ai_generated, template_based, unclear",
            "confidence": "0..1",
            "evidence": [
                {
                    "repo": "must equal repo",
                    "file": "file from snippets",
                    "lines": "lines from snippets",
                    "excerpt": "verbatim substring from snippet (<=200 chars)",
                    "reasoning": "one sentence"
                }
            ],
            "notes": "short string"
        },
        "rules": [
            "If you use labels tutorial_clone/copy_paste/ai_generated, include >=1 evidence item.",
            "If you label original with confidence >=0.6, include >=1 evidence item showing custom logic.",
            "Evidence must match (repo,file,lines) exactly as provided."
        ],
    }

    resp = llm.invoke([
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(user)},
    ]).content

    data = _safe_json_parse(resp) or {}

    score = float(data.get("authenticity_score", 50.0))
    score = max(0.0, min(100.0, score))

    labels = data.get("labels") or ["unclear"]
    if not isinstance(labels, list):
        labels = ["unclear"]
    labels = [str(x) for x in labels][:6]

    conf = float(data.get("confidence", 0.5))
    conf = max(0.0, min(1.0, conf))

    ev_raw = data.get("evidence") or []
    ev_items: List[Evidence] = []
    if isinstance(ev_raw, list):
        for x in ev_raw[:4]:
            if isinstance(x, dict):
                ev_items.append({
                    "repo": str(x.get("repo", repo_full)),
                    "file": str(x.get("file", "")),
                    "lines": str(x.get("lines", "")),
                    "excerpt": str(x.get("excerpt", "")),
                    "reasoning": str(x.get("reasoning", "")),
                })

    verified = verify_evidence(ev_items, ctx_lookup)

    if any(l in ("tutorial_clone", "copy_paste", "ai_generated") for l in labels) and not verified:
        labels = ["unclear"]
        conf = 0.0

    notes = str(data.get("notes", ""))[:240]

    return {
        "scan_mode": "deep",
        "authenticity_score": score,
        "labels": labels,
        "confidence": conf,
        "signals": signals,
        "evidence": verified,
        "notes": notes,
    }


def choose_deep_repos(repos: List[Dict[str, Any]], referenced_norm: set, k: int) -> List[Dict[str, Any]]:
    """
    Prioritize:
      - referenced repos (normalized match)
      - non-forks
      - larger repos (more substance)
      - some stars
    """
    def score(r: Dict[str, Any]) -> float:
        full = r.get("full_name") or ""
        full_norm = normalize_repo_full_name(full) or ""
        s = 0.0
        if full_norm and full_norm in referenced_norm:
            s += 1000.0
        if not r.get("fork"):
            s += 30.0
        s += min(60.0, (float(r.get("size") or 0)) / 200.0)  # size is KB
        if r.get("stargazers_count"):
            s += min(10.0, float(r.get("stargazers_count") or 0) / 5.0)
        return s

    ranked = sorted(repos, key=score, reverse=True)
    return ranked[:k]


def n_load(state: GraphState) -> GraphState:
    state.setdefault("meta", {})
    state["meta"]["loaded_at"] = time.time()
    return state


def n_extract(state: GraphState) -> GraphState:
    cv = state["cv_json"]
    state.setdefault("meta", {})

    if not state.get("github_user"):
        state["github_user"] = extract_github_username(cv)

    refs = extract_referenced_repos(cv)
    state["referenced_repos"] = refs
    state["meta"]["github_user_found"] = bool(state.get("github_user"))
    state["meta"]["referenced_repo_count"] = len(refs)
    return state


def n_collect_repos(state: GraphState) -> GraphState:
    state.setdefault("meta", {})
    user = state.get("github_user")
    if not user:
        state["repos_all"] = []
        state["repos_deep"] = []
        state["chunks"] = []
        state["chunk_vectors"] = None
        state["repo_slices"] = {}
        state["meta"]["notes"] = "No GitHub username found; cannot analyze authenticity."
        return state

    gh = GitHubPublic()

    repos_user, meta = gh.list_repos_all(user, max_repos=MAX_REPOS_TOTAL)
    state["meta"]["pages_fetched"] = meta.get("pages_fetched", 0)
    state["meta"]["rate_limited"] = bool(meta.get("rate_limited", False))

    referenced_norm = set(state.get("referenced_repos") or [])
    repos_extra: List[Dict[str, Any]] = []
    for norm_key in referenced_norm:
        meta_r = gh.get_repo(norm_key)
        if meta_r:
            repos_extra.append(meta_r)

    merged: Dict[str, Dict[str, Any]] = {}
    for r in repos_extra + repos_user:
        full = r.get("full_name") or ""
        k = normalize_repo_full_name(full)
        if k:
            merged[k] = r

    repos_all = list(merged.values())
    repos_all = sorted(repos_all, key=lambda x: x.get("pushed_at") or "", reverse=True)

    state["repos_all"] = repos_all
    state["meta"]["repos_total_seen"] = len(repos_all)

    repos_deep = choose_deep_repos(repos_all, referenced_norm, k=min(MAX_REPOS_DEEP, len(repos_all)))
    state["repos_deep"] = repos_deep
    state["meta"]["repos_deep_selected"] = len(repos_deep)

    return state


def n_deep_index(state: GraphState) -> GraphState:
    state.setdefault("meta", {})
    repos_deep = state.get("repos_deep") or []
    if not repos_deep:
        state["chunks"] = []
        state["chunk_vectors"] = None
        state["repo_slices"] = {}
        return state

    gh = GitHubPublic()

    all_chunks: List[Dict[str, Any]] = []
    repo_slices: Dict[str, Tuple[int, int]] = {}
    zip_fail = 0

    for r in repos_deep:
        full = r.get("full_name")
        branch = r.get("default_branch") or "main"
        if not full:
            continue

        zipb = cache_get(full, branch)
        if zipb is None:
            ok = False
            backoff = HTTP_BACKOFF
            for _ in range(HTTP_RETRIES):
                try:
                    zipb = gh.download_zipball(full, branch)
                    cache_set(full, branch, zipb)
                    ok = True
                    break
                except Exception:
                    time.sleep(backoff + random.random() * 0.2)
                    backoff *= 2
            if not ok:
                zip_fail += 1
                continue

        start = len(all_chunks)
        repo_chunks = build_chunks_from_zip(zipb, full, state["meta"])
        all_chunks.extend(repo_chunks)
        end = len(all_chunks)
        repo_slices[full] = (start, end)

        if len(all_chunks) >= MAX_TOTAL_CHUNKS:
            break

    state["chunks"] = all_chunks
    state["repo_slices"] = repo_slices
    state["meta"]["chunks"] = len(all_chunks)
    state["meta"]["zip_failures"] = zip_fail

    if not all_chunks:
        state["chunk_vectors"] = None
        return state

    emb = OpenAIEmbeddings(model=EMBED_MODEL)
    texts = [c["text"][:2500] for c in all_chunks]
    state["chunk_vectors"] = embed_texts(emb, texts, batch=64)
    state["meta"]["embedding_dim"] = int(state["chunk_vectors"].shape[1])

    return state

def n_features(state: GraphState) -> GraphState:
    state.setdefault("meta", {})
    repos_all = state.get("repos_all") or []
    chunks = state.get("chunks") or []
    slices = state.get("repo_slices") or {}

    deep_set_norm = set()
    for r in (state.get("repos_deep") or []):
        k = normalize_repo_full_name(r.get("full_name") or "")
        if k:
            deep_set_norm.add(k)

    referenced_norm = set(state.get("referenced_repos") or [])

    sim_counts: Dict[int, int] = {}
    sim_by_chunk: List[int] = []
    boiler_by_chunk: List[float] = []

    for c in chunks:
        h = simhash64(c["text"])
        sim_by_chunk.append(h)
        sim_counts[h] = sim_counts.get(h, 0) + 1
        boiler_by_chunk.append(chunk_is_boilerplate(c["text"]))

    signals_by_repo: Dict[str, Dict[str, Any]] = {}

    for r in repos_all:
        full = r.get("full_name") or ""
        if not full:
            continue
        full_norm = normalize_repo_full_name(full) or ""

        base = {
            "referenced_in_cv": (full_norm in referenced_norm),
            "is_fork": bool(r.get("fork")),
            "stars": int(r.get("stargazers_count") or 0),
            "forks": int(r.get("forks_count") or 0),
            "watchers": int(r.get("watchers_count") or 0),
            "size_kb": int(r.get("size") or 0),
            "open_issues": int(r.get("open_issues_count") or 0),
            "has_pages": bool(r.get("has_pages")),
            "has_wiki": bool(r.get("has_wiki")),
            "archived": bool(r.get("archived")),
            "disabled": bool(r.get("disabled")),
            "created_at": r.get("created_at"),
            "pushed_at": r.get("pushed_at"),
            "updated_at": r.get("updated_at"),
            "language": r.get("language"),
            "description": r.get("description"),
            "homepage": r.get("homepage"),
            "scan_mode": "deep" if (full_norm in deep_set_norm) else "shallow",
        }

        if full in slices:
            a, b = slices[full]
            repo_chunks = chunks[a:b]
            if repo_chunks:
                dupe = 0
                for i in range(a, b):
                    if sim_counts.get(sim_by_chunk[i], 0) > 1:
                        dupe += 1
                duplication_rate = dupe / max(1, (b - a))
                boiler = float(np.mean(boiler_by_chunk[a:b])) if (b - a) > 0 else 0.0

                files = {}
                def_hits = 0
                for c in repo_chunks:
                    files[c["file"]] = 1
                    if re.search(r"\b(def|class|function|export\s+default|public\s+class)\b", c["text"]):
                        def_hits += 1

                base.update({
                    "chunks_indexed": int(len(repo_chunks)),
                    "file_count_indexed": int(len(files)),
                    "duplication_rate_internal": round(float(duplication_rate), 4),
                    "boilerplate_score": round(float(boiler), 4),
                    "nontrivial_logic_rate": round(float(def_hits / max(1, len(repo_chunks))), 4),
                })

        signals_by_repo[full] = base

    state["signals_by_repo"] = signals_by_repo
    state["meta"]["signals_repos"] = len(signals_by_repo)
    return state

def n_judge(state: GraphState) -> GraphState:
    state.setdefault("meta", {})
    repos_all = state.get("repos_all") or []
    repos_deep = state.get("repos_deep") or []

    deep_set = set((r.get("full_name") or "") for r in repos_deep)

    chunks = state.get("chunks") or []
    vecs: Optional[np.ndarray] = state.get("chunk_vectors")
    slices = state.get("repo_slices") or {}
    signals_by_repo = state.get("signals_by_repo") or {}

    decisions: Dict[str, RepoAuthenticity] = {}

    for r in repos_all:
        full = r.get("full_name") or ""
        if not full:
            continue
        if full in deep_set:
            continue

        score, labels, conf, notes = quick_shallow_score(r)
        decisions[full] = {
            "scan_mode": "shallow",
            "authenticity_score": score,
            "labels": labels,
            "confidence": conf,
            "signals": signals_by_repo.get(full, {}),
            "evidence": [],
            "notes": notes,
        }

    if vecs is None or not chunks:
        state["decisions_by_repo"] = decisions
        state["meta"]["notes"] = (state["meta"].get("notes") or "") + " Deep index missing; only shallow scoring used."
        return state

    llm = ChatOpenAI(model=LLM_MODEL, temperature=0, timeout=LLM_TIMEOUT)
    emb = OpenAIEmbeddings(model=EMBED_MODEL)

    for r in repos_deep:
        full = r.get("full_name") or ""
        if not full or full not in slices:
            continue

        a, b = slices[full]
        repo_chunks = chunks[a:b]
        repo_vecs = vecs[a:b]
        if len(repo_chunks) == 0:
            continue

        signals = signals_by_repo.get(full, {})

        q_core = embed_query(emb, "core business logic, main functionality, algorithms, model training, API routes, custom code")
        idx_core = cosine_topk(repo_vecs, q_core, k=min(max(6, TOP_DEEP_SNIPPETS - 4), len(repo_chunks)))

        boiler_scores = []
        for i, c in enumerate(repo_chunks):
            boiler_scores.append((chunk_is_boilerplate(c["text"]), i))
        boiler_scores.sort(reverse=True)
        idx_boiler = [i for _, i in boiler_scores[:2]]

        idx_rand = random.sample(range(len(repo_chunks)), k=min(2, len(repo_chunks)))

        idx_all = []
        for i in list(idx_core) + idx_boiler + idx_rand:
            if int(i) not in idx_all:
                idx_all.append(int(i))
        idx_all = idx_all[:TOP_DEEP_SNIPPETS]
        contexts = [repo_chunks[i] for i in idx_all]

        decision = llm_judge_repo(llm, full, r, signals, contexts)

        if PENALIZE_FORKS and bool(r.get("fork")) and decision.get("authenticity_score", 50) > 70:
            decision["authenticity_score"] = max(0.0, float(decision["authenticity_score"]) - 10.0)
            if "template_based" not in (decision.get("labels") or []):
                decision["labels"] = (decision.get("labels") or []) + ["template_based"]
            decision["notes"] = (decision.get("notes") or "")[:220]

        decisions[full] = decision

    state["decisions_by_repo"] = decisions
    state["meta"]["judged_repos_total"] = len(decisions)
    state["meta"]["judged_repos_deep"] = sum(1 for d in decisions.values() if d.get("scan_mode") == "deep")
    state["meta"]["judged_repos_shallow"] = sum(1 for d in decisions.values() if d.get("scan_mode") == "shallow")
    return state

def n_assemble(state: GraphState) -> GraphState:
    decisions = state.get("decisions_by_repo") or {}
    referenced_norm = set(state.get("referenced_repos") or [])

    scores = []
    weights = []
    for repo_full, d in decisions.items():
        s = float(d.get("authenticity_score", 50.0))
        scan_mode = str(d.get("scan_mode", "shallow"))
        w = 2.0 if scan_mode == "deep" else 1.0

        repo_norm = normalize_repo_full_name(repo_full) or ""
        if repo_norm and repo_norm in referenced_norm:
            w += 1.0

        scores.append(s * w)
        weights.append(w)

    overall = (sum(scores) / max(1e-9, sum(weights))) if scores else 0.0

    out = {
        "github_user": state.get("github_user"),
        "overall_authenticity_score": round(float(overall), 2),
        "repos": decisions,
        "meta": state.get("meta", {}),
    }

    out["meta"]["repos_total_seen"] = state.get("meta", {}).get("repos_total_seen", 0)
    out["meta"]["repos_deep_selected"] = state.get("meta", {}).get("repos_deep_selected", 0)
    out["meta"]["referenced_repo_count"] = state.get("meta", {}).get("referenced_repo_count", 0)

    state["final_output"] = out
    state["meta"]["assembled_at"] = time.time()
    return state


def build_graph():
    g = StateGraph(GraphState)
    g.add_node("load", n_load)
    g.add_node("extract", n_extract)
    g.add_node("collect_repos", n_collect_repos)
    g.add_node("deep_index", n_deep_index)
    g.add_node("features", n_features)
    g.add_node("judge", n_judge)
    g.add_node("assemble", n_assemble)

    g.set_entry_point("load")
    g.add_edge("load", "extract")
    g.add_edge("extract", "collect_repos")
    g.add_edge("collect_repos", "deep_index")
    g.add_edge("deep_index", "features")
    g.add_edge("features", "judge")
    g.add_edge("judge", "assemble")
    g.add_edge("assemble", END)
    return g.compile()


def authenticate_projects(cv: dict):

    graph = build_graph()
    init: GraphState = {
        "cv_json": cv,
        "meta": {},
    }

    final_state = graph.invoke(init)
    out = final_state["final_output"]

    return out
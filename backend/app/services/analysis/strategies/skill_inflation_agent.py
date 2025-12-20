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

# =========================
# Config (env overridable)
# =========================
MAX_REPOS_TOTAL = 200   # list up to this many repos for the user
MAX_REPOS_DEEP = 18      # deep scan only these (zip + embeddings)
TOP_SKILL_SNIPPETS = 12

MAX_ZIP_BYTES_PER_REPO = 6_000_000
MAX_FILES_PER_REPO = 140
MAX_FILE_BYTES = 900_000
MAX_TOTAL_CHUNKS = 7000

CHUNK_MAX_LINES = 140
CHUNK_OVERLAP = 25

LLM_MODEL = "gpt-4o-mini"
EMBED_MODEL = "text-embedding-3-small"
LLM_TIMEOUT = 75

CACHE_DIR = ".cache/github_zip"
CACHE_TTL_SECONDS = 24 * 3600

HTTP_RETRIES = 3
HTTP_BACKOFF = 0.7


# =========================
# Output types
# =========================
class Evidence(TypedDict, total=False):
    repo: str
    file: str
    lines: str
    excerpt: str
    reasoning: str


class SkillClaim(TypedDict, total=False):
    skill: str                 # "Kubernetes"
    claim_text: str            # the exact phrasing from CV (if available)
    claimed_level: str         # "beginner|intermediate|expert|unknown"
    source: str                # "skills" | "projects" | "experience" | "summary" | "keywords" | "other"


class SkillDecision(TypedDict, total=False):
    claimed_level: str         # beginner|intermediate|expert|unknown
    observed_level: str        # beginner|intermediate|expert|unclear
    overclaim: bool
    severity: float            # 0..1 (how inflated)
    confidence: float          # 0..1
    evidence: List[Evidence]
    notes: str


class GraphState(TypedDict, total=False):
    cv_json: Dict[str, Any]
    github_user: Optional[str]

    repos_all: List[Dict[str, Any]]
    repos_deep: List[Dict[str, Any]]

    # deep index
    chunks: List[Dict[str, Any]]        # {"id","repo","file","start_line","end_line","text"}
    chunk_vectors: Any                  # np.ndarray (N,D)
    repo_slices: Dict[str, Tuple[int, int]]

    # skill claims
    claims: List[SkillClaim]
    decisions_by_skill: Dict[str, SkillDecision]

    meta: Dict[str, Any]
    final_output: Dict[str, Any]


# =========================
# CV helpers
# =========================
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

def extract_github_username(cv: Dict[str, Any]) -> Optional[str]:
    for s in find_all_strings(cv):
        if "github" not in s.lower():
            continue
        m = re.search(r"github\.com/([^/\s\)\]]+)", s, flags=re.IGNORECASE)
        if m:
            return m.group(1)
    return None


# =========================
# GitHub public client (no token)
# =========================
@dataclass
class GitHubPublic:
    user_agent: str = "public-cv-skill-inflation-agent/1.0"

    def _request(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: Tuple[int, int] = (10, 45),
    ) -> requests.Response:
        backoff = HTTP_BACKOFF
        last_exc: Optional[Exception] = None
        for _ in range(HTTP_RETRIES):
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

    def download_zipball(self, full_name: str, default_branch: str) -> bytes:
        url = f"https://api.github.com/repos/{full_name}/zipball/{default_branch}"
        r = self._request(url, timeout=(10, 90))
        if r.status_code != 200:
            raise RuntimeError(f"zipball download failed {full_name}@{default_branch}: {r.status_code}")
        return r.content


# =========================
# Zip cache
# =========================
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


# =========================
# Indexing code (deep repos only)
# =========================
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
        out.append((i + 1, j, "\n".join(lines[i:j])))
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

        path = "/".join(info.filename.split("/")[1:])  # strip top folder
        if not path or not should_keep(path):
            continue

        raw = z.read(info)
        total_bytes += len(raw)
        if total_bytes > MAX_ZIP_BYTES_PER_REPO:
            break

        text = raw.decode("utf-8", errors="ignore")
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


# =========================
# Embeddings + retrieval
# =========================
def embed_texts(emb: OpenAIEmbeddings, texts: List[str], batch: int = 64) -> np.ndarray:
    vecs: List[List[float]] = []
    for i in range(0, len(texts), batch):
        vecs.extend(emb.embed_documents(texts[i:i + batch]))
    return np.asarray(vecs, dtype=np.float32)

def embed_query(emb: OpenAIEmbeddings, q: str) -> np.ndarray:
    return np.asarray(emb.embed_query(q), dtype=np.float32)

def cosine_topk(M: np.ndarray, q: np.ndarray, k: int) -> np.ndarray:
    if M is None or len(M) == 0:
        return np.array([], dtype=int)
    qn = np.linalg.norm(q) + 1e-9
    Mn = np.linalg.norm(M, axis=1) + 1e-9
    sims = (M @ q) / (Mn * qn)
    k = min(k, len(sims))
    idx = np.argpartition(-sims, k - 1)[:k]
    return idx[np.argsort(-sims[idx])]


# =========================
# LLM helpers
# =========================
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


# =========================
# LLM: extract skill claims from CV JSON (no alias dict)
# =========================
def llm_extract_skill_claims(llm: ChatOpenAI, cv_json: Dict[str, Any]) -> List[SkillClaim]:
    system = (
        "You extract skill claims from a CV JSON.\n"
        "A skill claim may include level wording like beginner/intermediate/expert/senior/advanced.\n"
        "Return JSON only.\n"
        "Do NOT invent skills not present.\n"
        "If no explicit level is stated, claimed_level must be 'unknown'.\n"
    )
    user = {
        "cv_json": cv_json,
        "output_schema": {
            "claims": [
                {
                    "skill": "string (canonical name)",
                    "claim_text": "string (exact phrase from CV if possible)",
                    "claimed_level": "beginner|intermediate|expert|unknown",
                    "source": "skills|projects|experience|summary|keywords|other"
                }
            ]
        },
        "rules": [
            "If the CV says 'expert in X' => claimed_level='expert'.",
            "If the CV says 'advanced X' or 'senior' => claimed_level='expert'.",
            "If the CV says 'familiar with X' or 'basic X' => claimed_level='beginner'.",
            "If the CV only lists the skill name => claimed_level='unknown'.",
            "Prefer fewer, cleaner skills. Deduplicate."
        ]
    }

    resp = llm.invoke([
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(user)},
    ]).content

    data = _safe_json_parse(resp) or {}
    claims = data.get("claims") or []
    out: List[SkillClaim] = []

    if isinstance(claims, list):
        for c in claims[:200]:
            if not isinstance(c, dict):
                continue
            skill = str(c.get("skill", "")).strip()
            if not skill:
                continue
            cl = str(c.get("claimed_level", "unknown")).strip().lower()
            if cl not in ("beginner", "intermediate", "expert", "unknown"):
                cl = "unknown"
            out.append({
                "skill": skill,
                "claim_text": str(c.get("claim_text", "")).strip(),
                "claimed_level": cl,
                "source": str(c.get("source", "other")).strip()[:30] or "other",
            })

    # dedupe by skill (keep strongest claim if multiple)
    rank = {"expert": 3, "intermediate": 2, "beginner": 1, "unknown": 0}
    best: Dict[str, SkillClaim] = {}
    for c in out:
        k = c["skill"].strip().lower()
        if k not in best or rank.get(c["claimed_level"], 0) > rank.get(best[k]["claimed_level"], 0):
            best[k] = c
    return list(best.values())


# =========================
# LLM: compare claim vs code usage (observed level)
# =========================
def llm_assess_skill(
    llm: ChatOpenAI,
    claim: SkillClaim,
    contexts: List[Dict[str, Any]],
) -> SkillDecision:
    skill = claim["skill"]
    claimed_level = claim.get("claimed_level", "unknown")
    claim_text = claim.get("claim_text", "")

    # Build payload with strict evidence requirements
    ctx_payload = []
    ctx_lookup: Dict[str, str] = {}
    for c in contexts:
        lines = f"L{c['start_line']}-L{c['end_line']}"
        snippet = c["text"]
        if len(snippet) > 1800:
            snippet = snippet[:1800] + "\n…"
        key = f"{c['repo']}|{c['file']}|{lines}"
        ctx_payload.append({
            "repo": c["repo"],
            "file": c["file"],
            "lines": lines,
            "snippet": snippet,
        })
        ctx_lookup[key] = c["text"]

    system = (
        "You are a conservative evaluator for skill inflation.\n"
        "Goal: determine observed proficiency level from code usage evidence.\n"
        "Do NOT rely on the skill word appearing literally.\n"
        "Infer from patterns, APIs, configs, architecture, complexity, depth.\n"
        "Return JSON only. Evidence excerpts must be copied verbatim from snippets.\n"
        "Be cautious: if evidence is weak, observed_level='unclear'.\n"
    )

    user = {
        "skill": skill,
        "claim_text": claim_text,
        "claimed_level": claimed_level,
        "snippets": ctx_payload,
        "output_schema": {
            "observed_level": "beginner|intermediate|expert|unclear",
            "overclaim": "boolean",
            "confidence": "0..1",
            "evidence": [
                {
                    "repo": "string",
                    "file": "string",
                    "lines": "string like L10-L22",
                    "excerpt": "verbatim substring from snippet (<=200 chars)",
                    "reasoning": "one sentence"
                }
            ],
            "notes": "short string"
        },
        "rules": [
            "Beginner evidence: only minimal configs, trivial scripts, basic usage with defaults, small snippets.",
            "Intermediate evidence: integrates components, nontrivial configuration, error handling, structured modules, tests or CI.",
            "Expert evidence: advanced patterns, scalable architecture, operators/controllers, deep infra, robust deployment, custom tooling, performance/security considerations.",
            "If claimed_level is 'unknown', set overclaim=false unless evidence strongly contradicts a claim_text.",
            "If you mark overclaim=true, explain why observed is below claimed.",
            "Evidence must match repo/file/lines exactly as provided."
        ]
    }

    resp = llm.invoke([
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(user)},
    ]).content

    data = _safe_json_parse(resp) or {}
    observed = str(data.get("observed_level", "unclear")).lower().strip()
    if observed not in ("beginner", "intermediate", "expert", "unclear"):
        observed = "unclear"

    conf = float(data.get("confidence", 0.0))
    conf = max(0.0, min(1.0, conf))

    overclaim = bool(data.get("overclaim", False))
    notes = str(data.get("notes", ""))[:240]

    # Parse & verify evidence
    ev_raw = data.get("evidence") or []
    ev_items: List[Evidence] = []
    if isinstance(ev_raw, list):
        for x in ev_raw[:4]:
            if isinstance(x, dict):
                ev_items.append({
                    "repo": str(x.get("repo", "")),
                    "file": str(x.get("file", "")),
                    "lines": str(x.get("lines", "")),
                    "excerpt": str(x.get("excerpt", "")),
                    "reasoning": str(x.get("reasoning", "")),
                })
    verified = verify_evidence(ev_items, ctx_lookup)

    # If model says overclaim but provides no verified evidence -> downgrade
    if overclaim and not verified:
        overclaim = False
        conf = 0.0
        notes = (notes + " (downgraded: no verifiable evidence)")[:240]

    # severity mapping
    rank = {"beginner": 1, "intermediate": 2, "expert": 3, "unknown": 0, "unclear": 0}
    claimed_r = rank.get(claimed_level, 0)
    observed_r = rank.get(observed, 0)
    severity = 0.0
    if claimed_r > 0 and observed_r > 0 and claimed_r > observed_r:
        gap = claimed_r - observed_r
        severity = 0.6 if gap == 1 else 1.0
    elif overclaim and claimed_r > 0 and observed_r == 0:
        severity = 0.6  # conservative: unclear evidence but overclaim flagged (rare)

    return {
        "claimed_level": claimed_level,
        "observed_level": observed,
        "overclaim": bool(overclaim),
        "severity": float(max(0.0, min(1.0, severity))),
        "confidence": conf,
        "evidence": verified,
        "notes": notes,
    }


# =========================
# Deep repo selection
# =========================
def choose_deep_repos(repos: List[Dict[str, Any]], k: int) -> List[Dict[str, Any]]:
    """
    Prioritize:
      - recently pushed (repos already sorted by pushed_at desc)
      - non-forks
      - larger repos
      - starred a bit (weak)
    """
    def score(r: Dict[str, Any]) -> float:
        s = 0.0
        if not r.get("fork"):
            s += 30.0
        s += min(60.0, float(r.get("size") or 0) / 200.0)  # KB
        s += min(10.0, float(r.get("stargazers_count") or 0) / 5.0)
        return s

    ranked = sorted(repos, key=score, reverse=True)
    return ranked[:k]


# =========================
# LangGraph nodes
# =========================
def n_load(state: GraphState) -> GraphState:
    state.setdefault("meta", {})
    state["meta"]["loaded_at"] = time.time()
    return state

def n_extract(state: GraphState) -> GraphState:
    cv = state["cv_json"]
    state.setdefault("meta", {})

    if not state.get("github_user"):
        state["github_user"] = extract_github_username(cv)

    # LLM-based claim extraction (keeps claim wording)
    llm = ChatOpenAI(model=LLM_MODEL, temperature=0, timeout=LLM_TIMEOUT)
    claims = llm_extract_skill_claims(llm, cv)

    state["claims"] = claims
    state["meta"]["github_user_found"] = bool(state.get("github_user"))
    state["meta"]["claims_count"] = len(claims)
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
        state["meta"]["notes"] = "No GitHub username found; cannot verify skill usage."
        return state

    gh = GitHubPublic()
    repos_user, meta = gh.list_repos_all(user, max_repos=MAX_REPOS_TOTAL)
    state["meta"]["pages_fetched"] = meta.get("pages_fetched", 0)
    state["meta"]["rate_limited"] = bool(meta.get("rate_limited", False))

    # Dedup by full_name
    merged: Dict[str, Dict[str, Any]] = {}
    for r in repos_user:
        full = r.get("full_name") or ""
        if full:
            merged[full] = r

    repos_all = list(merged.values())
    repos_all = sorted(repos_all, key=lambda x: x.get("pushed_at") or "", reverse=True)
    state["repos_all"] = repos_all
    state["meta"]["repos_total_seen"] = len(repos_all)

    repos_deep = choose_deep_repos(repos_all, k=min(MAX_REPOS_DEEP, len(repos_all)))
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

def n_judge_skills(state: GraphState) -> GraphState:
    """
    For each skill claim:
      - retrieve relevant code snippets across ALL deep chunks
      - LLM assesses observed level and detects overclaim
    """
    state.setdefault("meta", {})
    claims = state.get("claims") or []
    chunks = state.get("chunks") or []
    vecs: Optional[np.ndarray] = state.get("chunk_vectors")

    decisions: Dict[str, SkillDecision] = {}

    if vecs is None or not chunks:
        for c in claims:
            sk = c["skill"]
            decisions[sk] = {
                "claimed_level": c.get("claimed_level", "unknown"),
                "observed_level": "unclear",
                "overclaim": False,
                "severity": 0.0,
                "confidence": 0.0,
                "evidence": [],
                "notes": "No code indexed; cannot compare against GitHub usage."
            }
        state["decisions_by_skill"] = decisions
        state["meta"]["notes"] = (state["meta"].get("notes") or "") + " Deep index missing; decisions set to unclear."
        return state

    llm = ChatOpenAI(model=LLM_MODEL, temperature=0, timeout=LLM_TIMEOUT)
    emb = OpenAIEmbeddings(model=EMBED_MODEL)

    # Precompute a small diversity pool to avoid “same repo always”
    N = len(chunks)
    rand_pool = random.sample(range(N), k=min(40, N))

    for claim in claims:
        skill = claim["skill"]

        # Retrieval query intentionally broad; no aliases dict; LLM will infer.
        query = (
            f"Evidence of real usage of skill '{skill}': "
            "configs, imports, APIs, deployment, infra, modules, tests, scripts, pipelines, "
            "nontrivial implementation details. Not just mention."
        )
        q = embed_query(emb, query)
        idx = cosine_topk(vecs, q, k=min(max(10, TOP_SKILL_SNIPPETS - 2), N)).tolist()

        # add a couple random snippets for context diversity
        for ri in rand_pool[:2]:
            if ri not in idx:
                idx.append(ri)

        idx = idx[:TOP_SKILL_SNIPPETS]
        contexts = [chunks[i] for i in idx]

        decisions[skill] = llm_assess_skill(llm, claim, contexts)

    state["decisions_by_skill"] = decisions
    state["meta"]["skills_judged"] = len(decisions)
    return state

def n_assemble(state: GraphState) -> GraphState:
    decisions = state.get("decisions_by_skill") or {}

    # overall inflation score: weighted mean of severities * 100, with confidence weighting
    sev_sum = 0.0
    w_sum = 0.0
    overclaim_count = 0

    for sk, d in decisions.items():
        sev = float(d.get("severity", 0.0))
        conf = float(d.get("confidence", 0.0))
        w = max(0.2, conf)  # keep some weight even if conservative
        sev_sum += sev * w
        w_sum += w
        if d.get("overclaim"):
            overclaim_count += 1

    inflation_score = 0.0
    if w_sum > 1e-9:
        inflation_score = (sev_sum / w_sum) * 100.0

    out = {
        "github_user": state.get("github_user"),
        "overall_skill_inflation_score": round(float(inflation_score), 2),  # higher = more inflation
        "overclaim_count": int(overclaim_count),
        "skills": decisions,
        "meta": state.get("meta", {}),
    }

    state["final_output"] = out
    state["meta"]["assembled_at"] = time.time()
    return state

def build_graph():
    g = StateGraph(GraphState)
    g.add_node("load", n_load)
    g.add_node("extract", n_extract)
    g.add_node("collect_repos", n_collect_repos)
    g.add_node("deep_index", n_deep_index)
    g.add_node("judge_skills", n_judge_skills)
    g.add_node("assemble", n_assemble)

    g.set_entry_point("load")
    g.add_edge("load", "extract")
    g.add_edge("extract", "collect_repos")
    g.add_edge("collect_repos", "deep_index")
    g.add_edge("deep_index", "judge_skills")
    g.add_edge("judge_skills", "assemble")
    g.add_edge("assemble", END)
    return g.compile()


def detect_skill_inflation(cv: dict):

    graph = build_graph()
    init: GraphState = {
        "cv_json": cv,
        "meta": {},
    }

    final_state = graph.invoke(init)
    out = final_state["final_output"]

    return out
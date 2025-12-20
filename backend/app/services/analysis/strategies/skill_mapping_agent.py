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

TOP_REPOS = 20
MAX_ZIP_BYTES_PER_REPO = 6_000_000
MAX_FILES_PER_REPO = 120
MAX_FILE_BYTES = 900_000
MAX_TOTAL_CHUNKS = 5000

CHUNK_MAX_LINES = 120
CHUNK_OVERLAP = 20

TOP_K = 15
LLM_MODEL = "gpt-4o-mini"
EMBED_MODEL = "text-embedding-3-small"

LLM_TIMEOUT = 75
MAX_JUDGE_RETRIES = 1

CACHE_DIR = ".cache/github_zip"
CACHE_TTL_SECONDS = 24 * 3600


# =========================
# Output schemas
# =========================
class Evidence(TypedDict, total=False):
    repo: str
    file: str
    lines: str
    excerpt: str
    reasoning: str


class SkillDecision(TypedDict, total=False):
    status: str            # supported | unsupported
    fake: bool             # True if unsupported
    confidence: float      # 0..1
    evidence: List[Evidence]


class GraphState(TypedDict, total=False):
    cv_json: Dict[str, Any]
    github_user: Optional[str]
    skills: List[str]

    repos: List[Dict[str, Any]]

    chunks: List[Dict[str, Any]]          # {"id","repo","file","start_line","end_line","text"}
    chunk_vectors: Any                    # np.ndarray (N,D)

    decisions: Dict[str, SkillDecision]
    meta: Dict[str, Any]
    final_output: Dict[str, Any]


# =========================
# CV utils (skills + github)
# =========================
def _clean(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)
    return s.strip("•- \t\r\n")

def uniq(xs: List[str]) -> List[str]:
    out, seen = [], set()
    for x in xs:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out

def extract_skills(cv: Dict[str, Any]) -> List[str]:
    skills: List[str] = []

    # 1) Extract from structured skills object (technical/tools/etc.)
    skills_obj = cv.get("skills")
    if isinstance(skills_obj, dict):
        for v in skills_obj.values():
            if isinstance(v, list):
                for x in v:
                    if isinstance(x, str):
                        skills.append(x)

    # 2) Extract from keywords (already flattened by LLM)
    keywords = cv.get("keywords")
    if isinstance(keywords, list):
        for x in keywords:
            if isinstance(x, str):
                skills.append(x)

    # 3) Extract from projects / experience metadata
    for section in (
        "projects", "experience", "education",
        "certifications", "awards", "volunteering", "publications"
    ):
        arr = cv.get(section)
        if not isinstance(arr, list):
            continue
        for it in arr:
            if not isinstance(it, dict):
                continue
            for sk_key in ("skills", "tech", "technologies", "stack", "keywords"):
                v = it.get(sk_key)
                if isinstance(v, list):
                    skills.extend([x for x in v if isinstance(x, str)])
                elif isinstance(v, str):
                    skills.extend([p.strip() for p in v.split(",")])

    # 4) Normalize
    skills = [_clean(s) for s in skills]
    skills = [s for s in skills if s and not re.fullmatch(r"\d+", s)]
    return uniq(skills)

def find_all_strings(obj: Any, limit: int = 20000) -> List[str]:
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
        if "github.com/" in s:
            m = re.search(r"github\.com/([^/\s\)\]]+)", s)
            if m:
                return m.group(1)
    return None


# =========================
# GitHub public client (no token)
# =========================
@dataclass
class GitHubPublic:
    user_agent: str = "public-cv-skill-evidence/llm-graph-1.0"

    def _get(self, url: str, params: Optional[Dict[str, Any]] = None, timeout: Tuple[int,int]=(10, 45)) -> requests.Response:
        return requests.get(url, params=params, headers={"User-Agent": self.user_agent}, timeout=timeout, allow_redirects=True)

    def list_repos(self, user: str, limit: int = TOP_REPOS) -> List[Dict[str, Any]]:
        url = f"https://api.github.com/users/{user}/repos"
        r = self._get(url, params={"per_page": 100, "sort": "pushed"}, timeout=(10, 30))
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, list):
            return []
        data = sorted(data, key=lambda x: x.get("pushed_at") or "", reverse=True)
        return data[:limit]

    def download_zipball(self, full_name: str, default_branch: str) -> bytes:
        url = f"https://api.github.com/repos/{full_name}/zipball/{default_branch}"
        r = self._get(url, timeout=(10, 90))
        r.raise_for_status()
        return r.content


# =========================
# Disk cache for zipballs
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
# Code indexing
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
    chunk_id = 0

    for info in z.infolist():
        if info.is_dir():
            continue

        if files_seen >= MAX_FILES_PER_REPO:
            break

        if info.file_size > MAX_FILE_BYTES:
            continue

        path = info.filename
        # strip GitHub top folder
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

        # make chunks
        for (s, e, ch) in chunk_text_lines(text):
            if not ch.strip():
                continue
            chunks.append({
                "id": f"{repo_full}:{path}:{s}-{e}:{chunk_id}",
                "repo": repo_full,
                "file": path,
                "start_line": s,
                "end_line": e,
                "text": ch,
            })
            chunk_id += 1
            if len(chunks) >= MAX_TOTAL_CHUNKS:
                return chunks

        files_seen += 1

    return chunks


# =========================
# Embedding index + retrieval
# =========================
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
    # cosine = (M·q)/(||M|| ||q||)
    qn = np.linalg.norm(q) + 1e-9
    Mn = np.linalg.norm(M, axis=1) + 1e-9
    sims = (M @ q) / (Mn * qn)
    idx = np.argpartition(-sims, min(k, len(sims)-1))[:k]
    idx = idx[np.argsort(-sims[idx])]
    return idx


# =========================
# LLM judge + verifier
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

def verify_evidence_items(items: List[Evidence], contexts_by_key: Dict[str, Dict[str, Any]]) -> List[Evidence]:
    """
    Evidence is valid if:
      - repo/file/lines reference an actually provided snippet
      - excerpt is a substring of the snippet text
      - line range string matches the snippet range format
    """
    verified: List[Evidence] = []
    for it in items:
        repo = (it.get("repo") or "").strip()
        file = (it.get("file") or "").strip()
        lines = (it.get("lines") or "").strip()
        excerpt = (it.get("excerpt") or "").strip()

        if not repo or not file or not lines or not excerpt:
            continue

        key = f"{repo}|{file}|{lines}"
        ctx = contexts_by_key.get(key)
        if not ctx:
            continue

        txt = ctx["text"]
        if excerpt not in txt:
            continue

        # keep excerpt short in final output
        it["excerpt"] = excerpt[:220]
        it["reasoning"] = (it.get("reasoning") or "")[:260]
        verified.append(it)

    return verified

def llm_judge_one_skill(
    llm: ChatOpenAI,
    skill: str,
    contexts: List[Dict[str, Any]],
) -> SkillDecision:
    # Provide snippets with stable keys so we can verify.
    ctx_payload = []
    ctx_lookup: Dict[str, Dict[str, Any]] = {}

    for c in contexts:
        repo = c["repo"]
        file = c["file"]
        lines = f"L{c['start_line']}-L{c['end_line']}"
        txt = c["text"]
        excerpt = txt
        if len(excerpt) > 1800:
            excerpt = excerpt[:1800] + "\n…"

        key = f"{repo}|{file}|{lines}"
        ctx_payload.append({
            "repo": repo,
            "file": file,
            "lines": lines,
            "snippet": excerpt,
        })
        ctx_lookup[key] = {"text": txt}

    system = (
        "You evaluate whether a claimed skill is supported by code evidence.\n"
        "Be conservative: supported only if snippets strongly imply real usage.\n"
        "Do NOT require the skill phrase to appear. Infer from libraries, architecture, APIs, patterns.\n"
        "You MUST cite evidence only from provided snippets (repo/file/lines must match exactly).\n"
        "Return JSON only."
    )

    user = {
        "skill": skill,
        "snippets": ctx_payload,
        "output_schema": {
            "status": "supported|unsupported",
            "confidence": "0..1",
            "evidence": [
                {
                    "repo": "repo from snippet",
                    "file": "file from snippet",
                    "lines": "lines from snippet",
                    "excerpt": "a short literal substring from that snippet (<=200 chars)",
                    "reasoning": "one sentence"
                }
            ]
        },
        "rules": [
            "If unsupported, evidence must be empty.",
            "If supported, include 1-3 evidence items.",
            "Excerpt MUST be copied verbatim from the snippet."
        ]
    }

    resp = llm.invoke([
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(user)},
    ]).content

    data = _safe_json_parse(resp) or {}
    status = str(data.get("status", "unsupported")).lower()
    supported = (status == "supported")
    conf = float(data.get("confidence", 0.0))
    conf = max(0.0, min(1.0, conf))

    raw_ev = data.get("evidence") or []
    ev_list: List[Evidence] = []
    if isinstance(raw_ev, list):
        for x in raw_ev[:3]:
            if isinstance(x, dict):
                ev_list.append({
                    "repo": str(x.get("repo", "")),
                    "file": str(x.get("file", "")),
                    "lines": str(x.get("lines", "")),
                    "excerpt": str(x.get("excerpt", "")),
                    "reasoning": str(x.get("reasoning", "")),
                })

    verified = verify_evidence_items(ev_list, ctx_lookup)

    # If model claimed supported but evidence doesn't verify -> downgrade.
    if supported and not verified:
        return {"status": "unsupported", "fake": True, "confidence": 0.0, "evidence": []}

    return {
        "status": "supported" if (supported and verified) else "unsupported",
        "fake": not (supported and verified),
        "confidence": conf if (supported and verified) else 0.0,
        "evidence": verified,
    }


# =========================
# LangGraph nodes
# =========================
def n_load(state: GraphState) -> GraphState:
    state.setdefault("meta", {})
    state["meta"]["loaded_at"] = time.time()
    return state

def n_extract(state: GraphState) -> GraphState:
    cv = state["cv_json"]
    state["skills"] = extract_skills(cv)
    if not state.get("github_user"):
        state["github_user"] = extract_github_username(cv)

    state.setdefault("meta", {})
    state["meta"]["skill_count"] = len(state["skills"])
    state["meta"]["github_user_found"] = bool(state.get("github_user"))
    return state

def n_collect_and_index(state: GraphState) -> GraphState:
    state.setdefault("meta", {})
    user = state.get("github_user")

    if not user:
        state["repos"] = []
        state["chunks"] = []
        state["chunk_vectors"] = None
        state["meta"]["notes"] = "No GitHub username found; cannot verify skills."
        return state

    gh = GitHubPublic()
    try:
        repos = gh.list_repos(user, limit=TOP_REPOS)
    except Exception as e:
        state["repos"] = []
        state["chunks"] = []
        state["chunk_vectors"] = None
        state["meta"]["notes"] = f"Failed to list repos: {e}"
        return state

    state["repos"] = repos

    all_chunks: List[Dict[str, Any]] = []
    zip_fail = 0
    for r in repos:
        full = r.get("full_name")
        branch = r.get("default_branch") or "main"
        if not full:
            continue

        zipb = cache_get(full, branch)
        if zipb is None:
            # retry a bit for flaky networks
            ok = False
            backoff = 0.7
            for _ in range(3):
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

        repo_chunks = build_chunks_from_zip(zipb, full, state["meta"])
        all_chunks.extend(repo_chunks)
        if len(all_chunks) >= MAX_TOTAL_CHUNKS:
            break

    state["chunks"] = all_chunks
    state["meta"]["chunks"] = len(all_chunks)
    state["meta"]["zip_failures"] = zip_fail

    if not all_chunks:
        state["chunk_vectors"] = None
        return state

    # Build embeddings index
    emb = OpenAIEmbeddings(model=EMBED_MODEL)
    texts = [c["text"][:2500] for c in all_chunks]  # cap for embedding
    vecs = embed_texts(emb, texts, batch=64)
    state["chunk_vectors"] = vecs
    state["meta"]["embedding_dim"] = int(vecs.shape[1])
    return state

def calculate_scores(skills: Dict[str, Any]) -> Dict[str, float]:
    total_score_sum = 0.0
    real_score_sum = 0.0
    real_skill_count = 0
    total_skill_count = len(skills)

    for skill_name, details in skills.items():
        score = details.get("confidence", 0.0)
        
        is_fake = details.get("fake", False)

        total_score_sum += score

        if not is_fake:
            real_score_sum += score
            real_skill_count += 1

    if total_skill_count > 0:
        all_skills_avg = total_score_sum / total_skill_count
    else:
        all_skills_avg = 0.0

    if real_skill_count > 0:
        real_skills_avg = real_score_sum / real_skill_count
    else:
        real_skills_avg = 0.0

    return {
        "total_skills_count": total_skill_count,
        "real_skills_count": real_skill_count,
        "fake_skills_count": total_skill_count - real_skill_count,
        "all_skills_avg": round(all_skills_avg, 4),
        "real_skills_avg": round(real_skills_avg, 4)
    }


def n_judge(state: GraphState) -> GraphState:
    state.setdefault("meta", {})
    skills = state.get("skills") or []
    chunks = state.get("chunks") or []
    vecs = state.get("chunk_vectors")

    decisions: Dict[str, SkillDecision] = {}

    if not chunks or vecs is None or len(chunks) != len(vecs):
        for sk in skills:
            decisions[sk] = {"status": "unsupported", "fake": True, "confidence": 0.0, "evidence": []}
        state["decisions"] = decisions
        state["meta"]["notes"] = (state["meta"].get("notes") or "") + " No indexed code; cannot verify."
        return state

    llm = ChatOpenAI(model=LLM_MODEL, temperature=0, timeout=LLM_TIMEOUT)
    emb = OpenAIEmbeddings(model=EMBED_MODEL)

    for sk in skills:
        # retrieval query: no aliases, just semantic search
        q = embed_query(emb, f"Evidence of skill: {sk}. Real usage in code, imports, APIs, architecture.")
        idx = cosine_topk(vecs, q, k=min(TOP_K, len(chunks)))
        ctx = [chunks[int(i)] for i in idx]

        # 1) judge
        decision = llm_judge_one_skill(llm, sk, ctx)

        # 2) if unsupported but we still suspect retrieval miss, retry once with a different query phrasing
        if decision["status"] == "unsupported" and MAX_JUDGE_RETRIES > 0:
            q2 = embed_query(emb, f"{sk} implementation, usage examples, libraries, patterns. Find strongest code proof.")
            idx2 = cosine_topk(vecs, q2, k=min(TOP_K, len(chunks)))
            ctx2 = [chunks[int(i)] for i in idx2]
            decision2 = llm_judge_one_skill(llm, sk, ctx2)
            # keep best (supported wins, else higher confidence)
            if decision2["status"] == "supported" or decision2.get("confidence", 0.0) > decision.get("confidence", 0.0):
                decision = decision2

        decisions[sk] = decision

    state["scores"] = calculate_scores(decisions)    
    state["decisions"] = decisions

    return state

def n_assemble(state: GraphState) -> GraphState:
    out = {
        "github_user": state.get("github_user"),
        "skills": state.get("decisions", {}),
        "scores": state.get("scores", {}),
        "meta": state.get("meta", {}),
    }
    state["final_output"] = out
    state["meta"]["assembled_at"] = time.time()
    return state


def build_graph():
    g = StateGraph(GraphState)
    g.add_node("load", n_load)
    g.add_node("extract", n_extract)
    g.add_node("collect_index", n_collect_and_index)
    g.add_node("judge", n_judge)
    g.add_node("assemble", n_assemble)

    g.set_entry_point("load")
    g.add_edge("load", "extract")
    g.add_edge("extract", "collect_index")
    g.add_edge("collect_index", "judge")
    g.add_edge("judge", "assemble")
    g.add_edge("assemble", END)
    return g.compile()


def skills_evidence_map(cv: dict):
    
    graph = build_graph()
    init: GraphState = {
        "cv_json": cv,
        "meta": {},
    }

    final_state = graph.invoke(init)
    out = final_state["final_output"]

    return out
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
MAX_SKILLS = 25                   
TOP_SNIPPETS_PER_SKILL = 10

MAX_ZIP_BYTES_PER_REPO = 6_000_000
MAX_FILES_PER_REPO = 160
MAX_FILE_BYTES = 900_000
MAX_TOTAL_CHUNKS = 7000

CHUNK_MAX_LINES = 140
CHUNK_OVERLAP = 25

LLM_MODEL = "gpt-4.1-mini"
EMBED_MODEL = "text-embedding-3-small"
LLM_TIMEOUT = 90

CACHE_DIR = ".cache/github_zip"
CACHE_TTL_SECONDS = 24 * 3600

HTTP_RETRIES = 3
HTTP_BACKOFF = 0.7


class SkillQuestions(TypedDict, total=False):
    claimed_level: str                 
    claim_quote: str                   
    evidence_level: str                
    overclaim: bool
    rationale: str                     
    theoretical: List[str]
    practical: List[str]
    debugging: List[str]
    focus_areas: List[str]             


class GraphState(TypedDict, total=False):
    cv_json: Dict[str, Any]
    github_user: Optional[str]

    repos_all: List[Dict[str, Any]]
    repos_deep: List[Dict[str, Any]]

    skills: List[str]

    chunks: List[Dict[str, Any]]               
    chunk_vectors: Any                         
    repo_slices: Dict[str, Tuple[int, int]]    

    claimed_levels: Dict[str, Dict[str, str]]  

    by_skill: Dict[str, SkillQuestions]
    summary: Dict[str, Any]
    meta: Dict[str, Any]
    final_output: Dict[str, Any]


def find_all_strings(obj: Any, limit: int = 40000) -> List[str]:
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
    """
    Lightweight skills extraction from your CV JSON schema (skills/keywords + sections).
    You can keep using your upstream JSON extraction agent to make this clean.
    """
    skills: List[str] = []

    v = cv.get("keywords")
    if isinstance(v, list):
        skills.extend([x for x in v if isinstance(x, str)])

    skills_obj = cv.get("skills")
    if isinstance(skills_obj, dict):
        for k in ("technical", "tools", "soft"):
            vv = skills_obj.get(k)
            if isinstance(vv, list):
                skills.extend([x for x in vv if isinstance(x, str)])
        vv = skills_obj.get("languages")
        if isinstance(vv, list):
            for it in vv:
                if isinstance(it, str):
                    skills.append(it)
                elif isinstance(it, dict) and "name" in it:
                    skills.append(str(it["name"]))

    for section in ("projects", "experience", "education", "certifications", "awards", "volunteering", "publications"):
        arr = cv.get(section)
        if not isinstance(arr, list):
            continue
        for it in arr:
            if not isinstance(it, dict):
                continue
            for sk_key in ("skills", "tech", "technologies", "stack", "keywords"):
                vv = it.get(sk_key)
                if isinstance(vv, list):
                    skills.extend([x for x in vv if isinstance(x, str)])
                elif isinstance(vv, str):
                    skills.extend([p.strip() for p in vv.split(",")])

    skills = [_clean(x) for x in skills]
    skills = [x for x in skills if x and not re.fullmatch(r"\d+", x)]
    return uniq(skills)


@dataclass
class GitHubPublic:
    user_agent: str = "public-interview-q-agent/1.0"

    def _request(self, url: str, params: Optional[Dict[str, Any]] = None, timeout: Tuple[int, int] = (10, 60)) -> requests.Response:
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
        raise RuntimeError(f"HTTP request failed: {url}. Last error: {last_exc}")

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
                "repo": repo_full,
                "file": path,
                "start_line": s,
                "end_line": e,
                "text": ch,
            })
            if len(chunks) >= MAX_TOTAL_CHUNKS:
                return chunks

        files_seen += 1

    return chunks


def choose_deep_repos(repos: List[Dict[str, Any]], k: int) -> List[Dict[str, Any]]:
    """
    Prioritize non-forks, larger size, recent pushes.
    """
    def score(r: Dict[str, Any]) -> float:
        s = 0.0
        if not r.get("fork"):
            s += 50.0
        s += min(120.0, float(r.get("size") or 0) / 150.0)   # size in KB
        # small star nudge (weak signal)
        s += min(12.0, float(r.get("stargazers_count") or 0) / 3.0)
        return s

    ranked = sorted(repos, key=score, reverse=True)
    return ranked[:k]


def embed_texts(emb: OpenAIEmbeddings, texts: List[str], batch: int = 64) -> np.ndarray:
    vecs: List[List[float]] = []
    for i in range(0, len(texts), batch):
        part = texts[i:i+batch]
        vecs.extend(emb.embed_documents(part))
    return np.asarray(vecs, dtype=np.float32)


def embed_query(emb: OpenAIEmbeddings, q: str) -> np.ndarray:
    return np.asarray(emb.embed_query(q), dtype=np.float32)


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


def llm_extract_claims(llm: ChatOpenAI, skills: List[str], cv_strings: List[str]) -> Dict[str, Dict[str, str]]:
    """
    Ask LLM to infer claimed proficiency for each skill from CV wording.
    Returns: skill -> {"claimed_level": "...", "quote": "..."}
    """

    lines = [x.strip() for x in cv_strings if x and len(x.strip()) >= 8]
    lines = sorted(lines, key=lambda x: len(x), reverse=True)
    lines = lines[:220]  # cap

    payload = {
        "skills": skills,
        "cv_lines": lines,
        "levels": ["beginner", "intermediate", "expert", "unspecified"],
        "rules": [
            "Use only the provided CV lines.",
            "If a skill has no explicit proficiency wording, set level=unspecified and quote=''.",
            "If you find a claim, quote must be copied verbatim from a provided CV line.",
            "Return JSON: { skill: {claimed_level, quote} } for each skill."
        ],
    }

    system = (
        "You extract claimed proficiency levels from a CV. "
        "Be strict: only mark beginner/intermediate/expert if explicitly stated or strongly implied "
        "by wording like 'expert', 'advanced', 'senior', 'proficient', 'familiar', etc. "
        "Return JSON only."
    )

    resp = llm.invoke([
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(payload)},
    ]).content

    data = _safe_json_parse(resp) or {}
    out: Dict[str, Dict[str, str]] = {}
    for sk in skills:
        v = data.get(sk, {}) if isinstance(data, dict) else {}
        if not isinstance(v, dict):
            v = {}
        lvl = str(v.get("claimed_level", "unspecified")).lower()
        if lvl not in ("beginner", "intermediate", "expert", "unspecified"):
            lvl = "unspecified"
        quote = str(v.get("quote", "")).strip()
        out[sk] = {"claimed_level": lvl, "quote": quote[:260]}
    return out


def llm_generate_questions_for_skill(
    llm: ChatOpenAI,
    skill: str,
    claim: Dict[str, str],
    contexts: List[Dict[str, Any]],
) -> SkillQuestions:
    """
    Generate questions + determine evidence strength and overclaim likelihood based on provided snippets.
    """
    snippets = []
    for c in contexts:
        excerpt = c["text"]
        if len(excerpt) > 1600:
            excerpt = excerpt[:1600] + "\n…"
        snippets.append({
            "repo": c["repo"],
            "file": c["file"],
            "lines": f"L{c['start_line']}-L{c['end_line']}",
            "snippet": excerpt,
            "score": round(float(c.get("score", 0.0)), 4),
        })

    payload = {
        "skill": skill,
        "claimed_level": claim.get("claimed_level", "unspecified"),
        "claim_quote": claim.get("quote", ""),
        "snippets": snippets,
        "output_schema": {
            "claimed_level": "beginner|intermediate|expert|unspecified",
            "claim_quote": "string",
            "evidence_level": "none|weak|moderate|strong",
            "overclaim": "boolean",
            "rationale": "short string",
            "theoretical": ["..."],
            "practical": ["..."],
            "debugging": ["..."],
            "focus_areas": ["..."],
        },
        "rules": [
            "Use the snippets to infer what the candidate likely did with this skill; do not require keyword matches.",
            "Evidence level: none if snippets irrelevant; weak if only superficial usage; moderate if meaningful usage; strong if core logic.",
            "Overclaim: true if claimed_level is high but evidence_level is weak/none.",
            "Generate 3-5 questions per category (theoretical/practical/debugging).",
            "Questions should match the claimed_level (harder for expert), but if overclaim=true, include at least 2 'expose weak understanding' questions.",
            "Keep questions specific and interview-usable. Avoid huge multi-part questions.",
        ],
    }

    system = (
        "You generate personalized interview questions based on a claimed skill and code evidence. "
        "Be practical and grounded in the provided snippets. Return JSON only."
    )

    resp = llm.invoke([
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(payload)},
    ]).content

    data = _safe_json_parse(resp) or {}

    def _list(key: str, nmax: int) -> List[str]:
        v = data.get(key, [])
        if not isinstance(v, list):
            return []
        out = []
        for x in v:
            if isinstance(x, str) and x.strip():
                out.append(x.strip())
        return out[:nmax]

    claimed_level = str(data.get("claimed_level", claim.get("claimed_level", "unspecified"))).lower()
    if claimed_level not in ("beginner", "intermediate", "expert", "unspecified"):
        claimed_level = "unspecified"

    evidence_level = str(data.get("evidence_level", "none")).lower()
    if evidence_level not in ("none", "weak", "moderate", "strong"):
        evidence_level = "none"

    overclaim = bool(data.get("overclaim", False))
    rationale = str(data.get("rationale", "")).strip()[:260]
    focus = _list("focus_areas", 8)

    out: SkillQuestions = {
        "claimed_level": claimed_level,
        "claim_quote": str(data.get("claim_quote", claim.get("quote", "")))[:260],
        "evidence_level": evidence_level,
        "overclaim": overclaim,
        "rationale": rationale,
        "theoretical": _list("theoretical", 6),
        "practical": _list("practical", 6),
        "debugging": _list("debugging", 6),
        "focus_areas": focus,
    }
    return out


def n_load(state: GraphState) -> GraphState:
    state.setdefault("meta", {})
    state["meta"]["loaded_at"] = time.time()
    return state


def n_extract(state: GraphState) -> GraphState:
    state.setdefault("meta", {})
    cv = state["cv_json"]

    if not state.get("github_user"):
        state["github_user"] = extract_github_username(cv)

    skills = extract_skills(cv)

    if len(skills) > MAX_SKILLS:
        skills = skills[:MAX_SKILLS]
    state["skills"] = skills

    state["meta"]["github_user_found"] = bool(state.get("github_user"))
    state["meta"]["skill_count"] = len(skills)
    return state


def n_collect_repos(state: GraphState) -> GraphState:
    state.setdefault("meta", {})
    user = state.get("github_user")
    if not user:
        state["repos_all"] = []
        state["repos_deep"] = []
        state["meta"]["notes"] = "No GitHub username found; questions will be CV-only."
        return state

    gh = GitHubPublic()
    repos, meta = gh.list_repos_all(user, max_repos=MAX_REPOS_TOTAL)
    state["repos_all"] = repos
    state["meta"]["pages_fetched"] = meta.get("pages_fetched", 0)
    state["meta"]["rate_limited"] = bool(meta.get("rate_limited", False))
    state["meta"]["repos_total_seen"] = len(repos)

    state["repos_deep"] = choose_deep_repos(repos, k=min(MAX_REPOS_DEEP, len(repos)))
    state["meta"]["repos_deep_selected"] = len(state["repos_deep"])
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


def n_claims(state: GraphState) -> GraphState:
    """
    CV-only: infer claimed proficiency per skill.
    """
    state.setdefault("meta", {})
    skills = state.get("skills") or []
    cv_lines = find_all_strings(state["cv_json"])

    llm = ChatOpenAI(model=LLM_MODEL, temperature=0, timeout=LLM_TIMEOUT)
    state["claimed_levels"] = llm_extract_claims(llm, skills, cv_lines)
    return state


def n_generate(state: GraphState) -> GraphState:
    """
    Per skill:
    - retrieve relevant code snippets (if indexed)
    - ask LLM to produce question sets (+ evidence strength + weak point)
    """
    state.setdefault("meta", {})
    skills = state.get("skills") or []
    claimed = state.get("claimed_levels") or {}

    chunks = state.get("chunks") or []
    vecs: Optional[np.ndarray] = state.get("chunk_vectors")

    llm = ChatOpenAI(model=LLM_MODEL, temperature=0, timeout=LLM_TIMEOUT)

    by_skill: Dict[str, SkillQuestions] = {}

    emb = OpenAIEmbeddings(model=EMBED_MODEL) if (vecs is not None and chunks) else None

    for sk in skills:
        claim = claimed.get(sk, {"claimed_level": "unspecified", "quote": ""})

        contexts: List[Dict[str, Any]] = []
        if vecs is not None and chunks and emb is not None:
            q1 = embed_query(emb, f"{sk}: core logic, implementation details, usage in code, libraries, architecture")
            idx1 = cosine_topk(vecs, q1, k=min(max(6, TOP_SNIPPETS_PER_SKILL - 4), len(chunks)))

            q2 = embed_query(emb, f"{sk}: errors, debugging, edge cases, performance, reliability, tests")
            idx2 = cosine_topk(vecs, q2, k=min(4, len(chunks)))

            idx_all = []
            for i in list(idx1) + list(idx2):
                ii = int(i)
                if ii not in idx_all:
                    idx_all.append(ii)
            idx_all = idx_all[:TOP_SNIPPETS_PER_SKILL]

            q = q1
            qn = np.linalg.norm(q) + 1e-9
            Mn = np.linalg.norm(vecs, axis=1) + 1e-9
            sims = (vecs @ q) / (Mn * qn)

            for i in idx_all:
                c = dict(chunks[i])
                c["score"] = float(sims[i])
                contexts.append(c)

            contexts.sort(key=lambda x: x.get("score", 0.0), reverse=True)

        by_skill[sk] = llm_generate_questions_for_skill(llm, sk, claim, contexts)

    state["by_skill"] = by_skill
    return state


def n_summary(state: GraphState) -> GraphState:
    """
    Create a short summary: weak points + suggested focus ordering.
    """
    by_skill = state.get("by_skill") or {}
    weak = []
    strong = []

    for sk, info in by_skill.items():
        ev = (info.get("evidence_level") or "none")
        oc = bool(info.get("overclaim", False))
        lvl = info.get("claimed_level", "unspecified")
        if ev in ("none", "weak") or oc:
            weak.append((sk, lvl, ev, oc))
        else:
            strong.append((sk, lvl, ev, oc))

    weak.sort(key=lambda t: (not t[3], t[2] != "none"))

    state["summary"] = {
        "weak_points": [
            {"skill": sk, "claimed_level": lvl, "evidence_level": ev, "overclaim": oc}
            for sk, lvl, ev, oc in weak[:12]
        ],
        "strong_points": [
            {"skill": sk, "claimed_level": lvl, "evidence_level": ev}
            for sk, lvl, ev, _ in strong[:12]
        ],
    }
    return state


def n_assemble(state: GraphState) -> GraphState:
    out = {
        "github_user": state.get("github_user"),
        "skills": state.get("by_skill", {}),
        "summary": state.get("summary", {}),
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
    g.add_node("claims", n_claims)
    g.add_node("generate", n_generate)
    g.add_node("summary", n_summary)
    g.add_node("assemble", n_assemble)

    g.set_entry_point("load")
    g.add_edge("load", "extract")
    g.add_edge("extract", "collect_repos")
    g.add_edge("collect_repos", "deep_index")
    g.add_edge("deep_index", "claims")
    g.add_edge("claims", "generate")
    g.add_edge("generate", "summary")
    g.add_edge("summary", "assemble")
    g.add_edge("assemble", END)
    return g.compile()


def generate_interview_questions(cv: dict) -> Dict[str, Any]:

    graph = build_graph()
    init: GraphState = {
        "cv_json": cv,
        "meta": {},
    }
    final_state = graph.invoke(init)
    out = final_state["final_output"]

    return out


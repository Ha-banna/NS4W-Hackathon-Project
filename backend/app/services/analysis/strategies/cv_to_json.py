from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Callable
from dotenv import load_dotenv
from dataclasses import dataclass, field

load_dotenv()

DEFAULT_MODEL = "gpt-5.2"
TOOL_READ_PDF = "read_pdf"
TOOL_LLM_EXTRACT = "openai_extract"
TOOL_FALLBACK = "fallback_extract"

@dataclass
class Tool:
    name: str
    fn: Callable[..., Any]
    description: str = ""
    schema: Dict[str, Any] = field(default_factory=dict)

    def run(self, **kwargs) -> Any:
        return self.fn(**kwargs)


class Agent:
    def __init__(self, name: str, tools: List[Tool], max_steps: int = 4):
        self.name = name
        self.tools = {t.name: t for t in tools}
        self.max_steps = max_steps
        self.state: Dict[str, Any] = {}
        self.artifacts: Dict[str, Any] = {}

    def call_tool(self, name: str, **kwargs) -> Any:
        if name not in self.tools:
            raise KeyError(f"Tool '{name}' is not registered in agent '{self.name}'")
        return self.tools[name].run(**kwargs)
    
    def run(self, pdf_path: str) -> Dict[str, Any]:
        self.state.clear()
        self.artifacts.clear()

        # 1) Read PDF text
        cv_text = self.call_tool(TOOL_READ_PDF, pdf_path=pdf_path)
        if not cv_text.strip():
            # scanned PDF or empty
            return {
                "candidate": {},
                "skills": {},
                "experience": [],
                "education": [],
                "projects": [],
                "certifications": [],
                "awards": [],
                "publications": [],
                "volunteering": [],
                "keywords": [],
                "meta": {"source": "pdf", "notes": "Empty text (possibly scanned PDF)."},
            }

        # 2) Try OpenAI extraction; fallback to no-LLM if anything fails
        try:
            data = self.call_tool(TOOL_LLM_EXTRACT, cv_text=cv_text)
            if isinstance(data, dict) and data:
                data.setdefault("meta", {})
                data["meta"].setdefault("source", "openai")
                return data
        except Exception as e:
            self.state["openai_error"] = str(e)

        # 3) No-LLM fallback
        data = self.call_tool(TOOL_FALLBACK, cv_text=cv_text)
        data.setdefault("meta", {})
        data["meta"]["source"] = "fallback_no_llm"
        if "openai_error" in self.state:
            data["meta"]["notes"] = f"OpenAI failed; used fallback. Error: {self.state['openai_error']}"
        return data


def extract_text_from_pdf(pdf_path: str) -> str:
    # Prefer pypdf / PyPDF2 (text-based PDFs)
    try:
        try:
            from pypdf import PdfReader
        except Exception:
            from PyPDF2 import PdfReader

        reader = PdfReader(pdf_path)
        parts: List[str] = []
        for page in reader.pages:
            t = page.extract_text() or ""
            if t.strip():
                parts.append(t)

        links = extract_links_from_pdf(pdf_path)
        if links:
            parts.extend(links)      

        return "\n\n".join(parts).strip()
        
    except Exception:
        # Fallback: pdfplumber
        import pdfplumber
        parts = []
        with pdfplumber.open(pdf_path) as pdf:
            for p in pdf.pages:
                t = p.extract_text() or ""
                if t.strip():
                    parts.append(t)

        links = extract_links_from_pdf(pdf_path)
        if links:
            parts.extend(links)      

        return "\n\n".join(parts).strip()

def extract_links_from_pdf(pdf_path: str) -> List[str]:
    from pypdf import PdfReader

    reader = PdfReader(pdf_path)
    links = []

    for page in reader.pages:
        annots = page.get("/Annots")
        if not annots:
            continue

        for a in annots:
            obj = a.get_object()
            action = obj.get("/A")
            if not action:
                continue

            uri = action.get("/URI")
            if uri:
                links.append(uri)

    return list(dict.fromkeys(links))


# ----------------------------
# OpenAI Structured Outputs (JSON Schema)
# ----------------------------


CV_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "candidate", "skills", "experience", "education", "projects",
        "certifications", "awards", "publications", "volunteering",
        "keywords", "meta"
    ],
    "properties": {
        "candidate": {
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "full_name": {"type": "string"},
                "headline": {"type": "string"},
                "summary": {"type": "string"},
                "contact": {
                    "type": "object",
                    "additionalProperties": True,
                    "properties": {
                        "email": {"type": "string"},
                        "phone": {"type": "string"},
                    },
                },
                "links": {
                    "type": "array",
                    "items": {"type": "object", "additionalProperties": True},
                },
            },
        },
        "skills": {
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "technical": {"type": "array", "items": {"type": "string"}},
                "tools": {"type": "array", "items": {"type": "string"}},
                "soft": {"type": "array", "items": {"type": "string"}},
                "languages": {"type": "array", "items": {"type": "object", "additionalProperties": True}},
            },
        },

        "experience": {"type": "array", "items": {"type": "object", "additionalProperties": True}},
        "education": {"type": "array", "items": {"type": "object", "additionalProperties": True}},
        "projects": {"type": "array", "items": {"type": "object", "additionalProperties": True}},
        "certifications": {"type": "array", "items": {"type": "object", "additionalProperties": True}},
        "awards": {"type": "array", "items": {"type": "object", "additionalProperties": True}},
        "publications": {"type": "array", "items": {"type": "object", "additionalProperties": True}},
        "volunteering": {"type": "array", "items": {"type": "object", "additionalProperties": True}},

        "keywords": {"type": "array", "items": {"type": "string"}},
        "meta": {"type": "object", "additionalProperties": True},
    },
}


SYSTEM_PROMPT = (
    "Extract the CV into JSON only. Do not invent facts. "
    "If information is missing, use empty strings/lists/objects."
)

def openai_extract_cv(cv_text: str, model: str = DEFAULT_MODEL) -> Dict[str, Any]:
    """
    Requires:
      pip install openai
    Uses Responses API + Structured Outputs (json_schema).
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    prompt = (
        "Return JSON with keys: candidate, skills, experience, education, projects, "
        "certifications, awards, publications, volunteering, keywords, meta.\n\n"
        f"CV_TEXT:\n{cv_text}"
    )

    resp = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "cv",
                "strict": False,
                "schema": CV_SCHEMA,
            }
        },
        store=False,
    )

    data = json.loads(resp.output_text)
    if not isinstance(data, dict):
        raise RuntimeError("OpenAI returned non-object JSON")
    return data


# ----------------------------
# No-LLM fallback (heuristics)
# ----------------------------

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_URL_RE = re.compile(r"(https?://\S+|www\.\S+)")
_PHONE_RE = re.compile(r"(\+?\d[\d\s().-]{7,}\d)")

# NOTE:
# Fallback extraction guarantees output shape compatibility with CV_SCHEMA.
# Reliability is prioritized over completeness.
def fallback_extract(cv_text: str) -> Dict[str, Any]:
    lines = [l.strip() for l in cv_text.splitlines()]
    lines = [l for l in lines if l]

    full_name = ""
    for l in lines[:8]:
        if any(x in l.lower() for x in ["curriculum", "resume", "cv"]):
            continue
        if 1 <= len(l.split()) <= 5 and re.search(r"[A-Za-z]", l):
            full_name = l
            break

    email = _EMAIL_RE.search(cv_text)
    phone = _PHONE_RE.search(cv_text)
    urls = list(dict.fromkeys(_URL_RE.findall(cv_text)))

    skills = []
    for i, l in enumerate(lines):
        if l.lower() in {"skills", "technical skills", "skill set"}:
            chunk = "\n".join(lines[i+1:i+15])
            skills = split_skills(chunk)
            break

    return {
        "candidate": {
            "full_name": full_name,
            "contact": {
                "email": email.group(0) if email else "",
                "phone": phone.group(0) if phone else "",
            },
            "links": [{"label": "", "url": u} for u in urls],
        },
        "skills": {"technical": skills},
        "experience": [],
        "education": [],
        "projects": [],
        "certifications": [],
        "awards": [],
        "publications": [],
        "volunteering": [],
        "keywords": skills[:20],
        "meta": {"notes": "Heuristic extraction; expect missing fields."},
    }

def split_skills(text: str) -> List[str]:
    # split on commas, pipes, bullets
    raw = re.split(r"[,\u2022|\n;]+", text)
    out = []
    for x in raw:
        x = x.strip(" -\t")
        if 2 <= len(x) <= 40:
            out.append(x)
    # dedupe
    seen = set()
    final = []
    for s in out:
        k = s.lower()
        if k not in seen:
            seen.add(k)
            final.append(s)
    return final

def openai_tool(cv_text: str) -> Dict[str, Any]:
    return openai_extract_cv(cv_text, model=DEFAULT_MODEL)

def convert_cv_to_json(cv_path: str) -> Dict[str, Any]:
    """
    High-level pipeline entrypoint.

    Pipeline:
    1. Read PDF → raw text
    2. Extract structured CV via LLM
    3. Fallback to heuristics if LLM fails

    Returns:
        Normalized CV data matching CV_SCHEMA.
    """
    agent = Agent(
        name="cv_pdf_to_json",
        tools=[
            Tool(TOOL_READ_PDF, extract_text_from_pdf),
            Tool(TOOL_LLM_EXTRACT , openai_tool),
            Tool(TOOL_FALLBACK, fallback_extract),
        ],
        max_steps=4,
    )
    out = agent.run(cv_path)
    
    out = agent.run(cv_path)
    assert isinstance(out, dict), "Agent output must be a dict"
    return out
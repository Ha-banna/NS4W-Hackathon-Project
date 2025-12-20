from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

Json = Dict[str, Any]

@dataclass
class AnalysisContext:
    # shared artifact produced early
    cv_json: Json = field(default_factory=dict)

    # each strategy stores its JSON output here
    results: Dict[str, Json] = field(default_factory=dict)
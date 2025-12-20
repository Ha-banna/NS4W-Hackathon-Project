from __future__ import annotations

import inspect
from typing import List
import uuid

from app.services.analysis.context.analysis_context import AnalysisContext
from app.services.analysis.strategies.cv_to_json import convert_cv_to_json

async def run_pipeline(
    *,
    cv_path: str,
    run_id: uuid
) -> AnalysisContext:
    """
    Pipeline:
      1) Create context
      2) Run CV -> JSON first (fills ctx.cv_json)
      3) Run remaining strategies (each writes ctx.results[strategy.name] = json)
      4) Return context (caller can persist ctx to DB)
    """

    # 1) Create shared context for this run
    ctx = AnalysisContext()

    # 2) Run CV -> JSON first
    ctx.cv_json = convert_cv_to_json()

    return ctx
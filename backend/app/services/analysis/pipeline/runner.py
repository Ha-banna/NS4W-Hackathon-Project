from __future__ import annotations

import inspect
from typing import List
import uuid
from app.db import mongo 

from app.services.analysis.context.analysis_context import AnalysisContext
from app.services.analysis.strategies.cv_to_json import convert_cv_to_json
from app.services.analysis.strategies.project_authenticity_agent import authenticate_projects
from app.services.analysis.strategies.interview_questions_agent import generate_interview_questions
from app.services.analysis.strategies.skill_inflation_agent import detect_skill_inflation
from app.services.analysis.strategies.skill_mapping_agent import skills_evidence_map

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
    ctx.cv_json = convert_cv_to_json(cv_path)
    ctx.results["project_authenticity_agent"] = authenticate_projects(ctx.cv_json)
    ctx.results["interview_questions_agent"] = generate_interview_questions(ctx.cv_json)
    ctx.results["skill_inflation_agent"] = detect_skill_inflation(ctx.cv_json)
    ctx.results["skill_mapping_agent"] = skills_evidence_map(ctx.cv_json)

    mongo.db["cv_results"].insert_one({
        '_id': run_id,
        'cv': ctx.cv_json,
        'skill_evidence': ctx.results["skill_mapping_agent"],
        'projects_authenticity': ctx.results["project_authenticity_agent"],
        'skill_inflation': ctx.results["skill_inflation_agent"],
        'interview_questions': ctx.results["interview_questions_agent"]
    })

    return ctx
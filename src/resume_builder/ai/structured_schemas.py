"""Pydantic schemas for Gemini structured outputs."""

from typing import List, Optional
from pydantic import BaseModel, Field


class TailoredBullet(BaseModel):
    bullet_text: str = Field(description="Action verb + Technical implementation + Purpose/Outcome. No fabricated metrics.")
    action_verb: str = Field(description="Strong professional action verb used at the start")


class TailoredProject(BaseModel):
    project_id: str = Field(description="The unique project ID matching verified project")
    title: str = Field(description="Verified project title")
    subtitle: str = Field(description="Technologies used, matching verified stack")
    bullets: List[str] = Field(default_factory=list, description="Polished bullet points truthfully representing the candidate's implementation")


class TailoredResumeContent(BaseModel):
    professional_headline: str = Field(default="", description="Targeted 1-line professional headline, truthful to candidate skills")
    professional_summary: str = Field(default="", description="2-3 line concise summary tailored to JD, truthful to candidate facts")
    skills_category_order: List[str] = Field(default_factory=list, description="Order of skill categories prioritized for this role")
    tailored_projects: List[TailoredProject] = Field(default_factory=list, description="The 4 projects in the exact required order (Bearing Fault at #2)")
    relevant_certifications: List[str] = Field(default_factory=list, description="Verified certifications relevant to this application")
    change_summary_notes: List[str] = Field(default_factory=list, description="Explanation of tailoring decisions and keyword alignment")

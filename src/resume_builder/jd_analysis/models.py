"""Pydantic models for Job Description analysis and requirement mapping."""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class RequirementStatus(str, Enum):
    STRONG_MATCH = "STRONG MATCH"
    PARTIAL_MATCH = "PARTIAL MATCH"
    MISSING = "MISSING"
    UNSUPPORTED = "UNSUPPORTED"


class RequirementItem(BaseModel):
    category: str
    requirement: str
    status: RequirementStatus
    supporting_evidence: Optional[str] = None
    is_must_have: bool = True
    candidate_skills_matched: List[str] = Field(default_factory=list)


class JobDescription(BaseModel):
    raw_text: str
    company_name: str = "Target Company"
    job_title: str = "Software Engineer"
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    programming_languages: List[str] = Field(default_factory=list)
    frameworks_and_libraries: List[str] = Field(default_factory=list)
    databases: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    experience_level: Optional[str] = None
    education_requirements: Optional[str] = None
    domain_keywords: List[str] = Field(default_factory=list)


class RequirementMatrix(BaseModel):
    items: List[RequirementItem] = Field(default_factory=list)
    strong_match_count: int = 0
    partial_match_count: int = 0
    missing_count: int = 0
    unsupported_count: int = 0
    match_percentage: float = 0.0

    def get_matched_must_have(self) -> List[str]:
        return [
            item.requirement
            for item in self.items
            if item.is_must_have and item.status in (RequirementStatus.STRONG_MATCH, RequirementStatus.PARTIAL_MATCH)
        ]

    def get_missing_must_have(self) -> List[str]:
        return [
            item.requirement
            for item in self.items
            if item.is_must_have and item.status == RequirementStatus.MISSING
        ]

    def get_unsupported_skills(self) -> List[str]:
        return [
            item.requirement
            for item in self.items
            if item.status == RequirementStatus.UNSUPPORTED
        ]

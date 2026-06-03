from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EvidenceItem(BaseModel):
    claim: str = "not stated"
    evidence_text: str = "not stated"
    page: str = "not stated"
    how_to_use: str = "not stated"
    verification_needed: bool = True


class PaperCard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paper_id: str
    file_name: str
    title: str = "not stated"
    authors: list[str] = Field(default_factory=list)
    year: str = "not stated"
    journal_or_source: str = "not stated"

    research_question: str = "not stated"
    core_argument: str = "not stated"
    theoretical_framework: str = "not stated"

    data_source: str = "not stated"
    sample_period: str = "not stated"
    sample_scope: str = "not stated"

    methodology: str = "not stated"
    identification_strategy: str = "not stated"

    dependent_variable: str = "not stated"
    independent_variables: list[str] = Field(default_factory=list)
    control_variables: list[str] = Field(default_factory=list)

    main_findings: list[str] = Field(default_factory=list)
    robustness_checks: list[str] = Field(default_factory=list)
    mechanism_analysis: list[str] = Field(default_factory=list)

    limitations: list[str] = Field(default_factory=list)
    relationship_to_user_topic: str = "not stated"

    usable_for: list[str] = Field(default_factory=list)
    not_usable_for: list[str] = Field(default_factory=list)

    key_evidence: list[EvidenceItem] = Field(default_factory=list)
    citation_risk: Literal["low", "medium", "high"] = "medium"
    citation_risk_reason: str = "not stated"

    extraction_warnings: list[str] = Field(default_factory=list)


PAPER_CARD_JSON_SCHEMA = PaperCard.model_json_schema()


class DocumentReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    file_name: str
    file_type: str
    title: str = "not stated"
    summary: str = "not stated"
    key_points: list[str] = Field(default_factory=list)
    important_details: list[str] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)
    dates_or_periods: list[str] = Field(default_factory=list)
    methods_or_frameworks: list[str] = Field(default_factory=list)
    data_or_evidence: list[str] = Field(default_factory=list)
    useful_quotes_or_locations: list[str] = Field(default_factory=list)
    relation_to_user_topic: str = "not stated"
    tags: list[str] = Field(default_factory=list)
    search_keywords: list[str] = Field(default_factory=list)
    uncertainty_or_limits: list[str] = Field(default_factory=list)


DOCUMENT_REPORT_JSON_SCHEMA = DocumentReport.model_json_schema()

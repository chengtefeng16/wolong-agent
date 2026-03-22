# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

from typing import List, Optional, Dict
from pydantic import BaseModel


class SourceInfo(BaseModel):
    title: str
    url: str
    issuing_authority: Optional[str] = None
    regulation_id: Optional[str] = None
    effective_date: Optional[str] = None
    last_checked: Optional[str] = None
    mandatory: Optional[bool] = True
    waiver_possible: Optional[bool] = False
    penalty_description: Optional[str] = None


class RegulationMetadata(BaseModel):
    country: str
    regulation_version: str
    issuing_authority: str
    jurisdiction: str
    effective_date: Optional[str] = None
    last_review_date: Optional[str] = None
    review_cycle: Optional[str] = None
    data_confidence_level: Optional[str] = "official"


class RuleBlock(BaseModel):
    value: Optional[dict] = None
    sources: List[SourceInfo]


class OfficialRules(BaseModel):
    metadata: RegulationMetadata

    allowed_import: RuleBlock
    vehicle_age_limit: RuleBlock
    steering_requirement: RuleBlock
    emission_requirement: RuleBlock
    fuel_policy: RuleBlock
    engine_displacement_policy: Optional[RuleBlock] = None
    prohibited_vehicle_policy: RuleBlock
    certification_policy: RuleBlock
    tax_policy: RuleBlock
    usage_policy: RuleBlock
    port_policy: RuleBlock


class VehicleInput(BaseModel):
    model: str
    year: int
    vehicle_type: str
    fuel: str
    engine_displacement: float
    gcc_certified: bool = False
    steering: str
    emission_standard: str
    accident: bool = False
    flood_damage: bool = False


class OfficialResult(BaseModel):
    status: str
    triggered_rules: List[str]


class EvaluationResult(BaseModel):
    official_result: OfficialResult
    cost_estimation: Optional[dict] = None
    risk_analysis: Optional[List[dict]] = None



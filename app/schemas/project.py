from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# Shared properties
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None

# Properties to receive on project creation
class ProjectCreate(ProjectBase):
    project_code: str
    project_type: str = "货物"
    procurement_method: Optional[str] = None
    budget_amount: Optional[Decimal] = None
    department: Optional[str] = None
    priority: Optional[str] = "medium"
    risk_level: Optional[str] = "low"

# Properties to receive on project update
class ProjectUpdate(ProjectBase):
    project_code: Optional[str] = None
    project_type: Optional[str] = None
    procurement_method: Optional[str] = None
    budget_amount: Optional[Decimal] = None
    department: Optional[str] = None
    priority: Optional[str] = None
    risk_level: Optional[str] = None
    status: Optional[str] = None
    review_status: Optional[str] = None

# Properties shared by models stored in DB
class ProjectInDBBase(ProjectBase):
    id: int
    project_code: str
    project_type: str
    owner_id: int
    status: Optional[str] = "planning"
    review_status: Optional[str] = "pending"
    budget_amount: Optional[Decimal] = None
    department: Optional[str] = None
    priority: Optional[str] = "medium"
    risk_level: Optional[str] = "low"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

# Properties to return to client
class Project(ProjectInDBBase):
    pass

# Properties stored in DB
class ProjectInDB(ProjectInDBBase):
    pass


# Issue schemas
class IssueBase(BaseModel):
    title: str
    description: Optional[str] = None
    issue_type: str = "general"
    priority: str = "medium"
    severity: str = "low"

class IssueCreate(IssueBase):
    assigned_to: Optional[int] = None
    due_date: Optional[datetime] = None

class IssueUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    issue_type: Optional[str] = None
    priority: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[int] = None
    due_date: Optional[datetime] = None
    resolution: Optional[str] = None

class IssueInDBBase(IssueBase):
    id: int
    issue_number: str
    project_id: int
    reporter_id: int
    assigned_to: Optional[int] = None
    status: str = "open"
    due_date: Optional[datetime] = None
    resolution: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class Issue(IssueInDBBase):
    pass

class IssueInDB(IssueInDBBase):
    pass


# ProjectComparison schemas
class ProjectComparisonBase(BaseModel):
    comparison_type: str = "similarity"
    notes: Optional[str] = None

class ProjectComparisonCreate(ProjectComparisonBase):
    compared_project_id: int

class ProjectComparisonUpdate(BaseModel):
    comparison_type: Optional[str] = None
    status: Optional[str] = None
    similarity_score: Optional[float] = None
    comparison_result: Optional[str] = None
    notes: Optional[str] = None

class ProjectComparisonInDBBase(ProjectComparisonBase):
    id: int
    project_id: int
    compared_project_id: int
    analyst_id: int
    status: str = "pending"
    similarity_score: Optional[float] = None
    comparison_result: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class ProjectComparison(ProjectComparisonInDBBase):
    pass

class ProjectComparisonInDB(ProjectComparisonInDBBase):
    pass
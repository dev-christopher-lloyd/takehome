from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.workflow import WorkflowStatus


class WorkflowResponse(BaseModel):
    """
    Standard representation of a workflow run returned by the API.

    This mirrors the core columns on the WorkflowRun SQLAlchemy model.
    """

    id: int
    campaign_id: int
    status: WorkflowStatus
    started_at: datetime
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

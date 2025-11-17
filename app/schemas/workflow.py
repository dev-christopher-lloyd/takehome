from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_serializer
from app.models.workflow import WorkflowStatus


class WorkflowResponse(BaseModel):
  id: int
  campaign_id: int
  status: WorkflowStatus
  started_at: datetime
  finished_at: Optional[datetime] = None
  error_message: Optional[str] = None


  model_config = ConfigDict(from_attributes=True)

  @field_serializer("status")
  def serialize_status(self, value: WorkflowStatus, _info):
    return value.name

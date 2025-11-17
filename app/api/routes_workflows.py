from typing import List
from fastapi import APIRouter, HTTPException, status
from app.models.workflow import Workflow
from app.schemas.workflow import WorkflowResponse
from app.core.db import DbSession

router = APIRouter()


@router.get("", response_model=List[WorkflowResponse])
def list_workflows(
    db: DbSession,
) -> List[WorkflowResponse]:
  workflows = db.query(Workflow).all()
  return [workflow for workflow in workflows]


@router.get("/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(
    workflow_id: int,
    db: DbSession,
) -> WorkflowResponse:
  workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
  if not workflow:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Workflow {workflow_id} not found",
    )
  return workflow

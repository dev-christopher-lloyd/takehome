from typing import Generator, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.workflow import Workflow
from app.schemas.workflow import WorkflowResponse

router = APIRouter()


def get_db() -> Generator[Session, None, None]:
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()


@router.get("", response_model=List[WorkflowResponse])
def list_workflows(
    db: Session = Depends(get_db),
) -> List[WorkflowResponse]:
  workflows = db.query(Workflow).all()
  return [workflow for workflow in workflows]


@router.get("/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
) -> WorkflowResponse:
  workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
  if not workflow:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Workflow {workflow_id} not found",
    )
  return workflow

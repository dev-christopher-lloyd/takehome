from typing import Generator, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models.workflow import WorkflowRun
from app.schemas.workflow import WorkflowResponse

router = APIRouter()

def get_db() -> Generator[Session, None, None]:
    """
    Simple DB session dependency for this router.
    Defined here to avoid circular imports with app.main.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("", response_model=List[WorkflowResponse])
def list_workflows(
    db: Session = Depends(get_db),
) -> List[WorkflowResponse]:
    """
    Return all workflow runs.
    """
    workflows = db.query(WorkflowRun).all()
    return [workflow for workflow in workflows]

@router.get("/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
) -> WorkflowResponse:
    """
    Return a single workflow run by its ID.
    """
    workflow = db.query(WorkflowRun).filter(WorkflowRun.id == workflow_id).first()
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found",
        )
    return workflow

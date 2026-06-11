import os
from uuid import UUID
from celery import shared_task
from typing import Dict, Any, Optional

from app.tasks import celery_app, run_async
from app.database import AsyncSessionLocal
from app.utils.excel import ExcelService
from app.services.lead_service import LeadService
from app.services.file_service import FileService

async def _import_leads_task_async(task, file_path: str, default_source_id: Optional[str], default_assigned_to: Optional[str]) -> Dict[str, Any]:
    try:
        with open(file_path, "rb") as f:
            content = f.read()
            
        source_uuid = UUID(default_source_id) if default_source_id else None
        assigned_uuid = UUID(default_assigned_to) if default_assigned_to else None

        async with AsyncSessionLocal() as db:
            excel_service = ExcelService(db)
            result = await excel_service.import_leads_from_excel(
                content=content,
                default_source_id=source_uuid,
                default_assigned_to=assigned_uuid,
                task=task
            )
            
        if os.path.exists(file_path):
            os.remove(file_path)
            
        return result
    except Exception as e:
        task.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise e

async def _export_leads_task_async(task, user_id: str, status: Optional[str], source_id: Optional[str], assigned_to: Optional[str], search: Optional[str]) -> Dict[str, Any]:
    try:
        async with AsyncSessionLocal() as db:
            # Check user role inside the task or just fetch leads as admin to simplify, 
            # ideally we should pass user or use LeadService.
            # But let's build args:
            from app.models.user import User
            from sqlalchemy import select
            user = await db.scalar(select(User).where(User.id == UUID(user_id)))
            
            lead_service = LeadService(db)
            leads = await lead_service.list_leads_for_export(
                current_user=user,
                status=status,
                source_id=UUID(source_id) if source_id else None,
                assigned_to=UUID(assigned_to) if assigned_to else None,
                search=search
            )
            
            excel_service = ExcelService(db)
            excel_bytes = await excel_service.export_leads_to_excel(leads)
            
            # Upload to S3/MinIO using FileService to generate a download link
            file_service = FileService()
            url = await file_service.upload_bytes(
                content=excel_bytes,
                filename="leads_export.xlsx",
                folder="exports",
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            return {"download_url": url}
    except Exception as e:
        task.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise e

@celery_app.task(bind=True, name="tasks.import_leads")
def import_leads_task(self, file_path: str, default_source_id: Optional[str], default_assigned_to: Optional[str]):
    return run_async(_import_leads_task_async(self, file_path, default_source_id, default_assigned_to))

@celery_app.task(bind=True, name="tasks.export_leads")
def export_leads_task(self, user_id: str, status: Optional[str] = None, source_id: Optional[str] = None, assigned_to: Optional[str] = None, search: Optional[str] = None):
    return run_async(_export_leads_task_async(self, user_id, status, source_id, assigned_to, search))



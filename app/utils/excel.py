import io
from typing import List, Dict, Any, Optional
from uuid import UUID
import pandas as pd
from datetime import datetime
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.lead import Lead, LeadStatus
from app.models.lead_source import LeadSource
from app.models.unit import Unit, UnitStatus, FinishingType
from app.models.project import Project
from app.models.lead_requirement import PropertyType
from app.core.exceptions import BadRequestException


class ExcelService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def export_leads_to_excel(
        self,
        leads: List[Lead],
    ) -> bytes:
        """Export leads to Excel file."""
        data = []
        for lead in leads:
            data.append({
                "ID": str(lead.id),
                "Full Name": lead.full_name,
                "Phone": lead.phone,
                "Email": lead.email or "",
                "WhatsApp": lead.whatsapp_number or "",
                "Status": lead.status.value,
                "Lost Reason": lead.lost_reason or "",
                "Source": lead.source.name if lead.source else "",
                "Assigned To": lead.assigned_user.full_name if lead.assigned_user else "",
                "Created At": lead.created_at.isoformat(),
                "Updated At": lead.updated_at.isoformat(),
            })

        df = pd.DataFrame(data)
        output = io.BytesIO()
        df.to_excel(output, index=False, engine="openpyxl")
        output.seek(0)
        return output.getvalue()

    async def import_leads_from_excel(
        self,
        file: UploadFile,
        default_source_id: Optional[UUID] = None,
        default_assigned_to: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """Import leads from Excel file."""
        content = await file.read()
        df = pd.read_excel(io.BytesIO(content), engine="openpyxl")

        required_columns = ["Full Name", "Phone"]
        for col in required_columns:
            if col not in df.columns:
                raise BadRequestException(f"Missing required column: {col}")

        created = 0
        skipped = 0
        errors = []

        for idx, row in df.iterrows():
            try:
                full_name = str(row.get("Full Name", "")).strip()
                phone = str(row.get("Phone", "")).strip()

                if not full_name or not phone:
                    errors.append(f"Row {idx + 2}: Missing required fields")
                    skipped += 1
                    continue

                existing = await self.db.execute(
                    select(Lead).where(Lead.phone == phone, Lead.is_deleted == False)
                )
                if existing.scalar_one_or_none():
                    skipped += 1
                    continue

                source_id = default_source_id
                if "Source" in df.columns and pd.notna(row.get("Source")):
                    source_name = str(row["Source"]).strip()
                    source_result = await self.db.execute(
                        select(LeadSource).where(LeadSource.name == source_name)
                    )
                    source = source_result.scalar_one_or_none()
                    if source:
                        source_id = source.id

                status = LeadStatus.NEW
                if "Status" in df.columns and pd.notna(row.get("Status")):
                    status_value = str(row["Status"]).strip().lower()
                    try:
                        status = LeadStatus(status_value)
                    except ValueError:
                        pass

                new_lead = Lead(
                    full_name=full_name,
                    phone=phone,
                    email=str(row.get("Email", "")).strip() if pd.notna(row.get("Email")) else None,
                    whatsapp_number=str(row.get("WhatsApp", "")).strip() if pd.notna(row.get("WhatsApp")) else None,
                    status=status,
                    source_id=source_id,
                    assigned_to=default_assigned_to,
                )

                self.db.add(new_lead)
                created += 1

            except Exception as e:
                errors.append(f"Row {idx + 2}: {str(e)}")
                skipped += 1

        await self.db.commit()

        return {
            "created": created,
            "skipped": skipped,
            "errors": errors[:10],
            "total_errors": len(errors),
        }

    async def export_units_to_excel(
        self,
        units: List[Unit],
    ) -> bytes:
        """Export units to Excel file."""
        data = []
        for unit in units:
            data.append({
                "ID": str(unit.id),
                "Unit Number": unit.unit_number,
                "Project": unit.project.name if unit.project else "",
                "Developer": unit.project.developer.name if unit.project and unit.project.developer else "",
                "Property Type": unit.property_type.value,
                "Price": float(unit.price),
                "Area (sqm)": float(unit.area_sqm),
                "Bedrooms": unit.bedrooms,
                "Bathrooms": unit.bathrooms,
                "Floor": unit.floor or "",
                "Finishing": unit.finishing.value,
                "Status": unit.status.value,
                "Location": unit.project.location if unit.project else "",
                "City": unit.project.city if unit.project else "",
            })

        df = pd.DataFrame(data)
        output = io.BytesIO()
        df.to_excel(output, index=False, engine="openpyxl")
        output.seek(0)
        return output.getvalue()

    async def import_units_from_excel(
        self,
        file: UploadFile,
        project_id: UUID,
    ) -> Dict[str, Any]:
        """Import units from Excel file into a project."""
        project_result = await self.db.execute(
            select(Project).where(Project.id == project_id, Project.is_deleted == False)
        )
        project = project_result.scalar_one_or_none()
        if not project:
            raise BadRequestException("Project not found")

        content = await file.read()
        df = pd.read_excel(io.BytesIO(content), engine="openpyxl")

        required_columns = ["Unit Number", "Property Type", "Price", "Area (sqm)", "Bedrooms", "Bathrooms", "Finishing"]
        for col in required_columns:
            if col not in df.columns:
                raise BadRequestException(f"Missing required column: {col}")

        created = 0
        skipped = 0
        errors = []

        for idx, row in df.iterrows():
            try:
                unit_number = str(row.get("Unit Number", "")).strip()
                property_type_str = str(row.get("Property Type", "")).strip().lower()
                price = float(row.get("Price", 0))
                area_sqm = float(row.get("Area (sqm)", 0))
                bedrooms = int(row.get("Bedrooms", 0))
                bathrooms = int(row.get("Bathrooms", 0))
                finishing_str = str(row.get("Finishing", "")).strip().lower().replace(" ", "_")

                if not unit_number:
                    errors.append(f"Row {idx + 2}: Missing unit number")
                    skipped += 1
                    continue

                try:
                    property_type = PropertyType(property_type_str)
                except ValueError:
                    errors.append(f"Row {idx + 2}: Invalid property type: {property_type_str}")
                    skipped += 1
                    continue

                try:
                    finishing = FinishingType(finishing_str)
                except ValueError:
                    errors.append(f"Row {idx + 2}: Invalid finishing type: {finishing_str}")
                    skipped += 1
                    continue

                status = UnitStatus.AVAILABLE
                if "Status" in df.columns and pd.notna(row.get("Status")):
                    status_value = str(row["Status"]).strip().lower()
                    try:
                        status = UnitStatus(status_value)
                    except ValueError:
                        pass

                new_unit = Unit(
                    project_id=project_id,
                    unit_number=unit_number,
                    property_type=property_type,
                    price=price,
                    area_sqm=area_sqm,
                    bedrooms=bedrooms,
                    bathrooms=bathrooms,
                    floor=int(row.get("Floor")) if pd.notna(row.get("Floor")) else None,
                    finishing=finishing,
                    status=status,
                    notes=str(row.get("Notes", "")).strip() if pd.notna(row.get("Notes")) else None,
                )

                self.db.add(new_unit)
                created += 1

            except Exception as e:
                errors.append(f"Row {idx + 2}: {str(e)}")
                skipped += 1

        await self.db.commit()

        return {
            "created": created,
            "skipped": skipped,
            "errors": errors[:10],
            "total_errors": len(errors),
        }

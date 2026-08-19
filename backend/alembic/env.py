"""Alembic environment configuration for async migrations.

Supports Fase A's mixed Alembic layout:

* Main linear — the historic chain under ``backend/alembic/versions/``.
* Per-module branches — module migrations under
  ``backend/app/modules/<name>/migrations/versions/``.
"""

import asyncio
import os
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from app.config import settings

# Import all models to register them with Base.metadata
from app.core.agents.models import (  # noqa: F401
    Agent,
    AgentApprovalQueue,
    AgentAuditLog,
    AgentSession,
)
from app.core.auth.models import Clinic, ClinicMembership, User  # noqa: F401
from app.core.plugins.alembic_paths import discover_version_locations
from app.core.plugins.db_models import (  # noqa: F401
    ExternalId,
    ModuleOperationLog,
    ModuleRecord,
)
from app.database import Base

from app.modules.agenda.models import (
    Appointment,
    AppointmentTreatment,
    Cabinet,
)  # noqa: F401

from app.modules.billing.models import (
    Invoice,
    InvoiceHistory,
    InvoiceItem,
    InvoicePayment,
    InvoiceSeries,
    InvoiceSeriesHistory,
)  # noqa: F401

from app.modules.budget.models import (
    Budget,
    BudgetHistory,
    BudgetItem,
    BudgetSignature,
)  # noqa: F401

from app.modules.catalog.models import (
    TreatmentCatalogItem,
    TreatmentCategory,
    TreatmentOdontogramMapping,
    VatType,
)  # noqa: F401

from app.modules.media.models import (
    Document,
    MediaAttachment,
)  # noqa: F401

from app.modules.notifications.models import (
    ClinicChannelSettings,
    ClinicNotificationSettings,
    ClinicSmtpSettings,
    CommunicationMessage,
    NotificationPreference,
    NotificationTemplate,
)  # noqa: F401

from app.modules.odontogram.models import (
    OdontogramHistory,
    ToothRecord,
    Treatment,
    TreatmentTooth,
)  # noqa: F401

from app.modules.patient_timeline.models import PatientTimeline  # noqa: F401
from app.modules.patients.models import Patient  # noqa: F401

from app.modules.patients_clinical.models import (
    Allergy,
    EmergencyContact,
    LegalGuardian,
    MedicalContext,
    Medication,
    SurgicalHistory,
    SystemicDisease,
)  # noqa: F401

from app.modules.payments.models import (
    PatientEarnedEntry,
    Payment,
    PaymentAllocation,
    PaymentHistory,
    Refund,
)  # noqa: F401

from app.modules.recalls.models import (
    Recall,
    RecallContactAttempt,
    RecallSettings,
)  # noqa: F401

from app.modules.schedules.models import (
    ClinicOverride,
    ClinicWeeklySchedule,
    ProfessionalOverride,
    ProfessionalWeeklySchedule,
    ScheduleShift,
)  # noqa: F401

from app.modules.treatment_plan.models import (
    PlannedTreatmentItem,
    TreatmentPlan,
)  # noqa: F401

from app.modules.whatsapp_kapso.models import (
    WhatsappKapsoSettings,
    WhatsappKapsoTemplate,
)  # noqa: F401


ALEMBIC_DIR = Path(__file__).parent
BACKEND_ROOT = ALEMBIC_DIR.parent
MAIN_LINEAR = ALEMBIC_DIR / "versions"
MODULES_ROOT = BACKEND_ROOT / "app" / "modules"

config = context.config


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

database_url = settings.DATABASE_URL

# Render normalmente entrega:
# postgresql://...
#
# Este proyecto utiliza SQLAlchemy ASYNC, por lo que necesitamos:
# postgresql+asyncpg://...
#
# Convertimos solamente si todavía no viene especificado el driver.

if database_url.startswith("postgresql://"):
    database_url = database_url.replace(
        "postgresql://",
        "postgresql+asyncpg://",
        1,
    )

elif database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://",
        "postgresql+asyncpg://",
        1,
    )

config.set_main_option(
    "sqlalchemy.url",
    database_url,
)


# ============================================================
# ALEMBIC VERSION LOCATIONS
# ============================================================

config.set_main_option(
    "version_locations",
    os.pathsep.join(
        discover_version_locations(
            MAIN_LINEAR,
            MODULES_ROOT,
        )
    ),
)


# ============================================================
# LOGGING
# ============================================================

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


target_metadata = Base.metadata


# ============================================================
# OFFLINE MIGRATIONS
# ============================================================

def run_migrations_offline() -> None:
    """Run migrations in offline mode."""

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named",
        },
    )

    with context.begin_transaction():
        context.run_migrations()


# ============================================================
# ONLINE MIGRATIONS
# ============================================================

def do_run_migrations(connection: Connection) -> None:
    """Run migrations with the given database connection."""

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations using SQLAlchemy async engine."""

    connectable = async_engine_from_config(
        config.get_section(
            config.config_ini_section,
            {},
        ),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(
            do_run_migrations
        )

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in online mode."""

    asyncio.run(
        run_async_migrations()
    )


# ============================================================
# ENTRY POINT
# ============================================================

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
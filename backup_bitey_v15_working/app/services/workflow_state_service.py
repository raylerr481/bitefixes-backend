"""
Bitey Workflow State Service V12

Responsible for:
- Start workflow state
- Retrieve active workflow
- Update workflow step
- Store collected workflow data
- Complete workflow
- Cancel workflow

Workflow state is conversational memory.
Tickets represent business work.
"""

from datetime import datetime
from typing import Dict, Any, Optional

from app.database.supabase import database


# =====================================================
# START WORKFLOW
# =====================================================

def start_workflow(
    company_id: int,
    customer_id: int,
    workflow: str,
    ticket_id: Optional[int] = None,
    data: Optional[Dict[str, Any]] = None
):

    try:

        state = {

            "company_id": company_id,

            "customer_id": customer_id,

            "ticket_id": ticket_id,

            "workflow": workflow,

            "step": 1,

            "status": "active",

            "data": data or {},

            "created_at": datetime.utcnow().isoformat(),

            "updated_at": datetime.utcnow().isoformat()

        }


        result = (

            database

            .table("workflow_states")

            .insert(state)

            .execute()

        )


        if result.data:

            return result.data[0]


        return None


    except Exception as error:

        print(
            "[START WORKFLOW ERROR]",
            error
        )

        return None



# =====================================================
# GET ACTIVE WORKFLOW
# =====================================================

def get_active_workflow(
    customer_id: int,
    company_id: Optional[int] = None
):

    try:

        query = (

            database

            .table("workflow_states")

            .select("*")

            .eq(
                "customer_id",
                customer_id
            )

            .eq(
                "status",
                "active"
            )

        )


        if company_id:

            query = query.eq(
                "company_id",
                company_id
            )


        result = (

            query

            .order(
                "created_at",
                desc=True
            )

            .limit(1)

            .execute()

        )


        if result.data:

            return result.data[0]


        return None


    except Exception as error:

        print(
            "[GET WORKFLOW ERROR]",
            error
        )

        return None



# =====================================================
# UPDATE STEP
# =====================================================

def update_workflow_step(
    workflow_id: int,
    step: int
):

    return update_workflow_state(

        workflow_id,

        {
            "step": step
        }

    )



# =====================================================
# SAVE DATA
# =====================================================

def save_workflow_data(
    workflow_id: int,
    key: str,
    value: Any
):

    try:

        current = get_workflow(
            workflow_id
        )


        if not current:

            return None


        data = current.get(
            "data",
            {}
        )


        data[key] = value


        return update_workflow_state(

            workflow_id,

            {
                "data": data
            }

        )


    except Exception as error:

        print(
            "[SAVE WORKFLOW DATA ERROR]",
            error
        )

        return None



# =====================================================
# GET WORKFLOW
# =====================================================

def get_workflow(
    workflow_id:int
):

    try:

        result = (

            database

            .table("workflow_states")

            .select("*")

            .eq(
                "id",
                workflow_id
            )

            .execute()

        )


        if result.data:

            return result.data[0]


        return None


    except Exception as error:

        print(
            "[GET WORKFLOW ID ERROR]",
            error
        )

        return None



# =====================================================
# UPDATE GENERIC
# =====================================================

def update_workflow_state(
    workflow_id:int,
    data:Dict[str,Any]
):

    try:

        data["updated_at"] = (
            datetime.utcnow()
            .isoformat()
        )


        result = (

            database

            .table("workflow_states")

            .update(data)

            .eq(
                "id",
                workflow_id
            )

            .execute()

        )


        if result.data:

            return result.data[0]


        return None


    except Exception as error:

        print(
            "[UPDATE WORKFLOW ERROR]",
            error
        )

        return None



# =====================================================
# COMPLETE
# =====================================================

def complete_workflow(
    workflow_id:int
):

    return update_workflow_state(

        workflow_id,

        {
            "status":
                "completed"
        }

    )



# =====================================================
# CANCEL
# =====================================================

def cancel_workflow(
    workflow_id:int
):

    return update_workflow_state(

        workflow_id,

        {
            "status":
                "cancelled"
        }

    )
# =====================================================
# START OR RESUME WORKFLOW V13
# Prevent duplicate active workflows
# =====================================================

def start_or_resume_workflow(
    company_id: int,
    customer_id: int,
    workflow: str,
    ticket_id: Optional[int] = None,
    data: Optional[Dict[str, Any]] = None
):
    try:

        existing = get_active_workflow(
            customer_id,
            company_id
        )


        if existing:

            if existing.get("workflow") == workflow:

                print(
                    "[WORKFLOW RESUME]",
                    existing
                )

                return {
                    "action": "resume",
                    "workflow": existing
                }


        new_state = start_workflow(
            company_id,
            customer_id,
            workflow,
            ticket_id,
            data
        )


        print(
            "[WORKFLOW START]",
            new_state
        )


        return {
            "action": "started",
            "workflow": new_state
        }


    except Exception as error:

        print(
            "[START OR RESUME WORKFLOW ERROR]",
            error
        )

        return None
from uuid import UUID

from fastapi import Depends, status, BackgroundTasks
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from rule_engine.exceptions import RuleError
from rule_engine.schemas import RuleSchema, BackendService
from rule_engine.services import RulesService
from utils.connection_handler import get_connection_handler_for_app, ConnectionHandler
from utils.serializers import ResponseData


def handle_rule_exception(response_data, exc: RuleError):
    response_data.success = False
    response_data.message = exc.message
    response_data.errors = [exc.detail]
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(response_data)
    )


async def get_plan_specific_rules(
        plan_id: UUID,
        connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    response_data = ResponseData.construct(success=True)
    try:
        rules_service = RulesService(connection_handler=connection_handler)
        rules = await rules_service.get_rules_by_plan(str(plan_id))
        response_data.data = rules
        return response_data

    except Exception as e:
        response_data.success = False
        response_data.message = f"Failed to fetch rules for plan {plan_id}"
        response_data.errors = [str(e)]
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=jsonable_encoder(response_data)
        )


async def add_rule_to_plan(
        plan_id: UUID,
        rule_id: UUID,
        background_task: BackgroundTasks,
        connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    response_data = ResponseData.construct(success=True)
    try:
        rules_service = RulesService(connection_handler=connection_handler)
        added_rule = await rules_service.add_rule_to_plan(plan_id, rule_id, background_task)
        response_data.data = added_rule
        return response_data

    except RuleError as e:
        return handle_rule_exception(response_data, e)

    except Exception as e:
        response_data.success = False
        response_data.message = f"Failed to add rule {rule_id} to plan {plan_id}"
        response_data.errors = [str(e)]
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=jsonable_encoder(response_data)
        )


async def create_rule(
        rule_details: RuleSchema,
        connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    response_data = ResponseData.construct(success=True)
    try:
        rules_service = RulesService(connection_handler=connection_handler)
        new_rule = await rules_service.create_rule(rule_details)
        response_data.data = new_rule
        return response_data

    except RuleError as e:
        return handle_rule_exception(response_data, e)

    except Exception as e:
        response_data.success = False
        response_data.message = "Failed to create rule"
        response_data.errors = [str(e)]
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=jsonable_encoder(response_data)
        )


async def remove_rule_from_plan(
        plan_id: UUID,
        rule_id: UUID,
        background_task: BackgroundTasks,
        connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    response_data = ResponseData.construct(success=True)
    try:
        rules_service = RulesService(connection_handler=connection_handler)
        await rules_service.remove_rule_from_plan(plan_id, rule_id, background_task)
        return response_data

    except RuleError as e:
        return handle_rule_exception(response_data, e)

    except Exception as e:
        response_data.success = False
        response_data.message = f"Failed to add rule {rule_id} to plan {plan_id}"
        response_data.errors = [str(e)]
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=jsonable_encoder(response_data)
        )


async def get_rules_with_conditions(
        plan_id: UUID,
        service_slug: BackendService,
        connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    response_data = ResponseData.construct(success=True)
    try:
        rules_service = RulesService(connection_handler=connection_handler)
        data = await rules_service.get_rules_with_conditions(plan_id, service_slug)
        response_data.data = data
        return response_data

    except RuleError as e:
        return handle_rule_exception(response_data, e)

    except Exception as e:
        response_data.success = False
        response_data.message = f"Failed to get rule for {service_slug} to plan {plan_id}"
        response_data.errors = [str(e)]
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=jsonable_encoder(response_data)
        )

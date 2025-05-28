from fastapi import Depends, Path, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from features.models import BackendService
from features.schemas import FeatureSchema, FeatureUpdateSchema
from features.services import FeaturesService
from features.exceptions import FeatureError

from utils.connection_handler import get_connection_handler_for_app, ConnectionHandler
from utils.serializers import ResponseData


async def get_all_features(
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app)
):
    response_data = ResponseData.construct(success=True)
    try:
        features_service = FeaturesService(connection_handler=connection_handler)
        features = await features_service.get_all_features()
        response_data.data = features
        return response_data
    except FeatureError as e:
        response_data.success = False
        response_data.message = e.message
        response_data.errors = [e.detail]
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=jsonable_encoder(response_data)
        )
    except Exception as e:
        response_data.success = False
        response_data.message = "Failed to fetch features"
        response_data.errors = [str(e)]
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=jsonable_encoder(response_data)
        )


async def create_feature(
    feature_details: FeatureSchema,
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    response_data = ResponseData.construct(success=True)
    try:
        features_service = FeaturesService(connection_handler=connection_handler)
        new_feature = await features_service.create_feature(feature_details)
        response_data.data = new_feature
        return response_data
    except FeatureError as e:
        response_data.success = False
        response_data.message = e.message
        response_data.errors = [e.detail]
        return JSONResponse(
            status_code=e.status_code,
            content=jsonable_encoder(response_data)
        )
    except Exception as e:
        response_data.success = False
        response_data.message = "Failed to create a new feature"
        response_data.errors = [str(e)]
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=jsonable_encoder(response_data)
        )


async def update_feature(
    feature_id: str,
    feature_details: FeatureUpdateSchema,
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    response_data = ResponseData.construct(success=True)
    try:
        features_service = FeaturesService(connection_handler=connection_handler)
        updated_feature = await features_service.update_feature(feature_id, feature_details)
        response_data.data = updated_feature
        return response_data
    except FeatureError as e:
        response_data.success = False
        response_data.message = e.message
        response_data.errors = [e.detail]
        return JSONResponse(
            status_code=e.status_code,
            content=jsonable_encoder(response_data)
        )
    except Exception as e:
        response_data.success = False
        response_data.message = "Failed to update the feature"
        response_data.errors = [str(e)]
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=jsonable_encoder(response_data)
        )


async def delete_feature(
    feature_id: str,
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    response_data = ResponseData.construct(success=True)
    try:
        features_service = FeaturesService(connection_handler=connection_handler)
        await features_service.delete_feature(feature_id)
        response_data.message = "Feature deleted successfully"
        return response_data
    except FeatureError as e:
        response_data.success = False
        response_data.message = e.message
        response_data.errors = [e.detail]
        return JSONResponse(
            status_code=e.status_code,
            content=jsonable_encoder(response_data)
        )
    except Exception as e:
        response_data.success = False
        response_data.message = "Failed to delete the feature"
        response_data.errors = [str(e)]
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=jsonable_encoder(response_data)
        )


async def get_features_for_plan(
    plan_id: str,
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    response_data = ResponseData.construct(success=True)
    try:
        features_service = FeaturesService(connection_handler=connection_handler)
        features = await features_service.get_features_for_plan(plan_id)
        response_data.data = features
        return response_data
    except FeatureError as e:
        response_data.success = False
        response_data.message = e.message
        response_data.errors = [e.detail]
        return JSONResponse(
            status_code=e.status_code,
            content=jsonable_encoder(response_data)
        )
    except Exception as e:
        response_data.success = False
        response_data.message = "Failed to fetch features for the plan"
        response_data.errors = [str(e)]
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=jsonable_encoder(response_data)
        )


async def add_feature_to_plan(
    plan_id: str,
    feature_id: str,
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    response_data = ResponseData.construct(success=True)
    try:
        features_service = FeaturesService(connection_handler=connection_handler)
        await features_service.add_feature_to_plan(plan_id, feature_id)
        response_data.message = "Feature added to plan successfully"
        return response_data
    except FeatureError as e:
        response_data.success = False
        response_data.message = e.message
        response_data.errors = [e.detail]
        return JSONResponse(
            status_code=e.status_code,
            content=jsonable_encoder(response_data)
        )
    except Exception as e:
        response_data.success = False
        response_data.message = "Failed to add feature to the plan"
        response_data.errors = [str(e)]
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=jsonable_encoder(response_data)
        )


async def remove_feature_from_plan(
    plan_id: str,
    feature_id: str,
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    response_data = ResponseData.construct(success=True)
    try:
        features_service = FeaturesService(connection_handler=connection_handler)
        await features_service.remove_feature_from_plan(plan_id, feature_id)
        response_data.message = "Feature removed from plan successfully"
        return response_data
    except FeatureError as e:
        response_data.success = False
        response_data.message = e.message
        response_data.errors = [e.detail]
        return JSONResponse(
            status_code=e.status_code,
            content=jsonable_encoder(response_data)
        )
    except Exception as e:
        response_data.success = False
        response_data.message = "Failed to remove feature from the plan"
        response_data.errors = [str(e)]
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=jsonable_encoder(response_data)
        )


async def get_features_by_service(
    service_name: str = Path(..., description="Name of the backend service"),
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app)
):
    response_data = ResponseData.construct(success=True)
    try:
        features_service = FeaturesService(connection_handler=connection_handler)
        service_enum = BackendService(service_name)
        features = await features_service.get_features_by_service(service_enum)
        response_data.data = features
        return response_data
    except FeatureError as e:
        response_data.success = False
        response_data.message = e.message
        response_data.errors = [e.detail]
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=jsonable_encoder(response_data)
        )
    except Exception as e:
        response_data.success = False
        response_data.message = "Failed to fetch features for the backend service"
        response_data.errors = [str(e)]
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=jsonable_encoder(response_data)
        )

#  Copyright (c) ZenML GmbH 2022. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at:
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
#  or implied. See the License for the specific language governing
#  permissions and limitations under the License.
"""Endpoint definitions for pipeline runs."""
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Security

from zenml.constants import (
    API,
    COMPONENT_SIDE_EFFECTS,
    GRAPH,
    PIPELINE_CONFIGURATION,
    RUNS,
    STATUS,
    STEPS,
    VERSION_1,
)
from zenml.enums import ExecutionStatus, PermissionType
from zenml.models import (
    PipelineRunFilterModel,
    PipelineRunResponseModel,
    PipelineRunUpdateModel,
    StepRunFilterModel,
    StepRunResponseModel,
)
from zenml.models.page_model import Page
from zenml.post_execution.lineage.lineage_graph import LineageGraph
from zenml.zen_server.auth import AuthContext, authorize
from zenml.zen_server.utils import (
    error_response,
    handle_exceptions,
    make_dependable,
    zen_store,
)

router = APIRouter(
    prefix=API + VERSION_1 + RUNS,
    tags=["runs"],
    responses={401: error_response},
)


@router.get(
    "",
    response_model=Page[PipelineRunResponseModel],
    responses={401: error_response, 404: error_response, 422: error_response},
)
@handle_exceptions
def list_runs(
    runs_filter_model: PipelineRunFilterModel = Depends(
        make_dependable(PipelineRunFilterModel)
    ),
    _: AuthContext = Security(authorize, scopes=[PermissionType.READ]),
) -> Page[PipelineRunResponseModel]:
    """Get pipeline runs according to query filters.

    Args:
        runs_filter_model: Filter model used for pagination, sorting,
                                   filtering

    Returns:
        The pipeline runs according to query filters.
    """
    return zen_store().list_runs(runs_filter_model=runs_filter_model)


@router.get(
    "/{run_id}",
    response_model=PipelineRunResponseModel,
    responses={401: error_response, 404: error_response, 422: error_response},
)
@handle_exceptions
def get_run(
    run_id: UUID,
    _: AuthContext = Security(authorize, scopes=[PermissionType.READ]),
) -> PipelineRunResponseModel:
    """Get a specific pipeline run using its ID.

    Args:
        run_id: ID of the pipeline run to get.

    Returns:
        The pipeline run.
    """
    return zen_store().get_run(run_name_or_id=run_id)


@router.put(
    "/{run_id}",
    response_model=PipelineRunResponseModel,
    responses={401: error_response, 404: error_response, 422: error_response},
)
@handle_exceptions
def update_run(
    run_id: UUID,
    run_model: PipelineRunUpdateModel,
    _: AuthContext = Security(authorize, scopes=[PermissionType.WRITE]),
) -> PipelineRunResponseModel:
    """Updates a run.

    Args:
        run_id: ID of the run.
        run_model: Run model to use for the update.

    Returns:
        The updated run model.
    """
    return zen_store().update_run(run_id=run_id, run_update=run_model)


@router.delete(
    "/{run_id}",
    responses={401: error_response, 404: error_response, 422: error_response},
)
@handle_exceptions
def delete_run(
    run_id: UUID,
    _: AuthContext = Security(authorize, scopes=[PermissionType.WRITE]),
) -> None:
    """Deletes a run.

    Args:
        run_id: ID of the run.
    """
    zen_store().delete_run(run_id=run_id)


@router.get(
    "/{run_id}" + GRAPH,
    response_model=LineageGraph,
    responses={401: error_response, 404: error_response, 422: error_response},
)
@handle_exceptions
def get_run_dag(
    run_id: UUID,
    _: AuthContext = Security(authorize, scopes=[PermissionType.READ]),
) -> LineageGraph:
    """Get the DAG for a given pipeline run.

    Args:
        run_id: ID of the pipeline run to use to get the DAG.

    Returns:
        The DAG for a given pipeline run.
    """
    from zenml.post_execution.pipeline_run import PipelineRunView

    run = zen_store().get_run(run_name_or_id=run_id)
    graph = LineageGraph()
    graph.generate_run_nodes_and_edges(PipelineRunView(run))
    return graph


@router.get(
    "/{run_id}" + STEPS,
    response_model=Page[StepRunResponseModel],
    responses={401: error_response, 404: error_response, 422: error_response},
)
@handle_exceptions
def get_run_steps(
    step_run_filter_model: StepRunFilterModel = Depends(
        make_dependable(StepRunFilterModel)
    ),
    _: AuthContext = Security(authorize, scopes=[PermissionType.READ]),
) -> Page[StepRunResponseModel]:
    """Get all steps for a given pipeline run.

    Args:
        step_run_filter_model: Filter model used for pagination, sorting,
            filtering

    Returns:
        The steps for a given pipeline run.
    """
    return zen_store().list_run_steps(step_run_filter_model)


@router.get(
    "/{run_id}" + COMPONENT_SIDE_EFFECTS,
    response_model=Dict,
    responses={401: error_response, 404: error_response, 422: error_response},
)
@handle_exceptions
def get_run_component_side_effects(
    run_id: UUID,
    component_id: Optional[UUID] = None,
    _: AuthContext = Security(authorize, scopes=[PermissionType.READ]),
) -> Dict[str, Any]:
    """Get the component side effects for a given pipeline run.

    Args:
        run_id: ID of the pipeline run to use to get the component side effects.
        component_id: ID of the component to use to get the component
            side effects.

    Returns:
        The component side effects for a given pipeline run.
    """
    return {}


@router.get(
    "/{run_id}" + PIPELINE_CONFIGURATION,
    response_model=Dict[str, Any],
    responses={401: error_response, 404: error_response, 422: error_response},
)
@handle_exceptions
def get_pipeline_configuration(
    run_id: UUID,
    _: AuthContext = Security(authorize, scopes=[PermissionType.READ]),
) -> Dict[str, Any]:
    """Get the pipeline configuration of a specific pipeline run using its ID.

    Args:
        run_id: ID of the pipeline run to get.

    Returns:
        The pipeline configuration of the pipeline run.
    """
    return zen_store().get_run(run_name_or_id=run_id).pipeline_configuration


@router.get(
    "/{run_id}" + STATUS,
    response_model=ExecutionStatus,
    responses={401: error_response, 404: error_response, 422: error_response},
)
@handle_exceptions
def get_run_status(
    run_id: UUID,
    _: AuthContext = Security(authorize, scopes=[PermissionType.READ]),
) -> ExecutionStatus:
    """Get the status of a specific pipeline run.

    Args:
        run_id: ID of the pipeline run for which to get the status.

    Returns:
        The status of the pipeline run.
    """
    return zen_store().get_run(run_id).status

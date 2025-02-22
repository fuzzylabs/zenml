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
"""Implementation for the BentoML inference service."""

import os
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from bentoml.client import Client
from pydantic import BaseModel, Field

from zenml.constants import DEFAULT_LOCAL_SERVICE_IP_ADDRESS
from zenml.integrations.bentoml.constants import (
    BENTOML_HEALTHCHECK_URL_PATH,
    BENTOML_PREDICTION_URL_PATH,
)
from zenml.logger import get_logger
from zenml.services import (
    HTTPEndpointHealthMonitor,
    HTTPEndpointHealthMonitorConfig,
    LocalDaemonService,
    LocalDaemonServiceConfig,
    LocalDaemonServiceEndpoint,
    LocalDaemonServiceEndpointConfig,
    ServiceEndpointProtocol,
    ServiceType,
)

if TYPE_CHECKING:

    from zenml.integrations.bentoml.model_deployers.bentoml_model_deployer import (  # noqa
        BentoMLModelDeployer,
    )

logger = get_logger(__name__)


class BentoMLDeploymentEndpointConfig(LocalDaemonServiceEndpointConfig):
    """BentoML deployment service configuration.

    Attributes:
        prediction_url_path: URI subpath for prediction requests
    """

    prediction_url_path: str


class BentoMLDeploymentEndpoint(LocalDaemonServiceEndpoint):
    """A service endpoint exposed by the BentoML deployment daemon.

    Attributes:
        config: service endpoint configuration
    """

    config: BentoMLDeploymentEndpointConfig
    monitor: HTTPEndpointHealthMonitor

    @property
    def prediction_url(self) -> Optional[str]:
        """Gets the prediction URL for the endpoint.

        Returns:
            the prediction URL for the endpoint
        """
        uri = self.status.uri
        if not uri:
            return None
        return os.path.join(uri, self.config.prediction_url_path)


class SSLBentoMLParametersConfig(BaseModel):
    """BentoML SSL parameters configuration.

    Attributes:
        ssl_certfile: SSL certificate file
        ssl_keyfile: SSL key file
        ssl_keyfile_password: SSL key file password
        ssl_version: SSL version
        ssl_cert_reqs: SSL certificate requirements
        ssl_ca_certs: SSL CA certificates
        ssl_ciphers: SSL ciphers
    """

    ssl_certfile: Optional[str] = None
    ssl_keyfile: Optional[str] = None
    ssl_keyfile_password: Optional[str] = None
    ssl_version: Optional[str] = None
    ssl_cert_reqs: Optional[str] = None
    ssl_ca_certs: Optional[str] = None
    ssl_ciphers: Optional[str] = None


class BentoMLDeploymentConfig(LocalDaemonServiceConfig):
    """BentoML model deployment configuration.

    Attributes:
        model_name: name of the model to deploy
        model_uri: URI of the model to deploy
        port: port to expose the service on
        bento: Bento package to deploy
        workers: number of workers to use
        backlog: number of requests to queue
        production: whether to run in production mode
        working_dir: working directory for the service
        host: host to expose the service on
        ssl_parameters: SSL parameters for the Bentoml deployment
    """

    model_name: str
    model_uri: str
    bento: str
    bento_uri: Optional[str] = None
    apis: List[str] = []
    workers: Optional[int] = None
    port: Optional[int] = None
    backlog: Optional[int] = None
    production: bool = False
    working_dir: str
    host: Optional[str] = None
    ssl_parameters: Optional[SSLBentoMLParametersConfig] = Field(
        default_factory=SSLBentoMLParametersConfig
    )


class BentoMLDeploymentService(LocalDaemonService):
    """BentoML deployment service used to start a local prediction server for BentoML models.

    Attributes:
        SERVICE_TYPE: a service type descriptor with information describing
            the BentoML deployment service class
        config: service configuration
        endpoint: optional service endpoint
    """

    SERVICE_TYPE = ServiceType(
        name="bentoml-deployment",
        type="model-serving",
        flavor="bentoml",
        description="BentoML prediction service",
    )

    config: BentoMLDeploymentConfig
    endpoint: BentoMLDeploymentEndpoint

    def __init__(
        self,
        config: Union[BentoMLDeploymentConfig, Dict[str, Any]],
        **attrs: Any,
    ) -> None:
        """Initialize the BentoML deployment service.

        Args:
            config: service configuration
            attrs: additional attributes to set on the service
        """
        # ensure that the endpoint is created before the service is initialized
        # TODO [ENG-700]: implement a service factory or builder for BentoML
        #   deployment services
        if (
            isinstance(config, BentoMLDeploymentConfig)
            and "endpoint" not in attrs
        ):

            endpoint = BentoMLDeploymentEndpoint(
                config=BentoMLDeploymentEndpointConfig(
                    protocol=ServiceEndpointProtocol.HTTP,
                    port=config.port,
                    ip_address=config.host or DEFAULT_LOCAL_SERVICE_IP_ADDRESS,
                    prediction_url_path=BENTOML_PREDICTION_URL_PATH,
                ),
                monitor=HTTPEndpointHealthMonitor(
                    config=HTTPEndpointHealthMonitorConfig(
                        healthcheck_uri_path=BENTOML_HEALTHCHECK_URL_PATH,
                    )
                ),
            )
            attrs["endpoint"] = endpoint
        super().__init__(config=config, **attrs)

    def run(self) -> None:
        """Start the service."""
        logger.info(
            "Starting BentoML prediction service as blocking "
            "process... press CTRL+C once to stop it."
        )

        self.endpoint.prepare_for_start()
        ssl_params = self.config.ssl_parameters or SSLBentoMLParametersConfig()
        # verify if to deploy in production mode or development mode
        if self.config.production:
            logger.info("Running in production mode.")
            from bentoml.serve import serve_http_production

            try:
                serve_http_production(
                    self.config.bento,
                    port=self.endpoint.status.port,
                    api_workers=self.config.workers,
                    backlog=self.config.backlog,
                    host=self.endpoint.status.hostname,
                    working_dir=self.config.working_dir,
                    ssl_certfile=ssl_params.ssl_certfile,
                    ssl_keyfile=ssl_params.ssl_keyfile,
                    ssl_keyfile_password=ssl_params.ssl_keyfile_password,
                    ssl_version=ssl_params.ssl_version,
                    ssl_cert_reqs=ssl_params.ssl_cert_reqs,
                    ssl_ca_certs=ssl_params.ssl_ca_certs,
                    ssl_ciphers=ssl_params.ssl_ciphers,
                )
            except KeyboardInterrupt:
                logger.info(
                    "BentoML prediction service stopped. Resuming normal execution."
                )
        else:
            logger.info("Running in development mode.")
            from bentoml.serve import serve_http_development

            try:
                serve_http_development(
                    self.config.bento,
                    port=self.endpoint.status.port,
                    working_dir=self.config.working_dir,
                    host=self.endpoint.status.hostname,
                    ssl_certfile=ssl_params.ssl_certfile,
                    ssl_keyfile=ssl_params.ssl_keyfile,
                    ssl_keyfile_password=ssl_params.ssl_keyfile_password,
                    ssl_version=ssl_params.ssl_version,
                    ssl_cert_reqs=ssl_params.ssl_cert_reqs,
                    ssl_ca_certs=ssl_params.ssl_ca_certs,
                    ssl_ciphers=ssl_params.ssl_ciphers,
                )
            except KeyboardInterrupt:
                logger.info(
                    "BentoML prediction service stopped. Resuming normal execution."
                )

    @property
    def prediction_url(self) -> Optional[str]:
        """Get the URI where the http server is running.

        Returns:
            The URI where the http service can be accessed to get more information
            about the service and to make predictions.
        """
        if not self.is_running:
            return None
        return self.endpoint.prediction_url

    @property
    def prediction_apis_urls(self) -> Optional[List[str]]:
        """Get the URI where the prediction api services is answering requests.

        Returns:
            The URI where the prediction service apis can be contacted to process
            HTTP/REST inference requests, or None, if the service isn't running.
        """
        if not self.is_running:
            return None

        if self.config.apis:
            return [
                f"{self.endpoint.prediction_url}/{api}"
                for api in self.config.apis
            ]
        return None

    def predict(self, api_endpoint: str, data: "Any") -> "Any":
        """Make a prediction using the service.

        Args:
            data: data to make a prediction on
            api_endpoint: the api endpoint to make the prediction on

        Returns:
            The prediction result.

        Raises:
            Exception: if the service is not running
            ValueError: if the prediction endpoint is unknown.
        """
        if not self.is_running:
            raise Exception(
                "BentoML prediction service is not running. "
                "Please start the service before making predictions."
            )
        if self.endpoint.prediction_url is not None:
            client = Client.from_url(self.endpoint.prediction_url)
            result = client.call(api_endpoint, data)
        else:
            raise ValueError("No endpoint known for prediction.")
        return result

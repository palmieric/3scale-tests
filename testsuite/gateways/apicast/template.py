"""Self managed apicast deployed from apicast template"""
import base64
import logging
from abc import ABC, abstractmethod
from typing import Optional, List
from urllib.parse import urlparse

from threescale_api.resources import Service
from testsuite.requirements import ThreeScaleAuthDetails
from .selfmanaged import SelfManagedApicast, SelfManagedApicastRequirements

LOGGER = logging.getLogger(__name__)


class TemplateApicastRequirements(SelfManagedApicastRequirements,
                                  ThreeScaleAuthDetails,
                                  ABC):
    """Requirements for TemplateApicast"""
    @property
    @abstractmethod
    def template(self):
        """Returns template file"""

    @property
    @abstractmethod
    def image(self):
        """Return image to use with in the template"""

    @property
    @abstractmethod
    def configuration_url(self):
        """Returns URL for configuring apicast"""

    @property
    @abstractmethod
    def service_routes(self) -> bool:
        """True, if apicast should creates route for every service"""


# pylint: disable=too-many-instance-attributes
class TemplateApicast(SelfManagedApicast):
    """Template-based Apicast Gateway."""

    def __init__(self, requirements: TemplateApicastRequirements) -> None:
        super().__init__(requirements)
        self.requirements = requirements
        self.openshift = requirements.current_openshift
        self.staging = requirements.staging
        self.template = requirements.template
        self.image = requirements.image
        self.service_routes = requirements.service_routes
        self.service_name = self.deployment
        self.configuration_url_secret_name = f'{self.deployment}-config-url'
        self.routes: List[str] = []

    def get_app_params(self, **kwargs):
        """Template envs for oc new-app."""
        params = {
            "APICAST_NAME": self.deployment,
            "AMP_APICAST_IMAGE": self.image,
            "DEPLOYMENT_ENVIRONMENT": "production",
            "CONFIGURATION_LOADER": "boot",
            "CONFIGURATION_CACHE": 300,
            "LOG_LEVEL": "debug",
            "CONFIGURATION_URL_SECRET": self.configuration_url_secret_name,
        }

        if self.staging:
            params.update({
                "CONFIGURATION_LOADER": "lazy",
                "DEPLOYMENT_ENVIRONMENT": "staging",
                "CONFIGURATION_CACHE": 0,
            })

        params.update(**kwargs)

        return params

    def _get_configuration_url_secret_resource(self):
        config_url = base64.b64encode(self.requirements.configuration_url).decode("utf-8")
        return {
            "kind": "Secret",
            "apiVersion": "v1",
            "metadata": {
                "name": self.configuration_url_secret_name,
            },
            "data": {
                "password": config_url,
            },
            "type": "kubernetes.io/basic-auth"
        }

    def _create_configuration_url_secret(self):
        if self.configuration_url_secret_name not in self.openshift.secrets:
            LOGGER.debug('Secret "%s" does not exist. Creating...', self.configuration_url_secret_name)

            self.openshift.apply(self._get_configuration_url_secret_resource())

    def _route_name(self, entity_id):
        if self.staging:
            return f"{entity_id}-staging"
        return f"{entity_id}-production"

    def on_service_create(self, service: Service):
        if self.service_routes:
            entity_id = service.entity_id
            self.add_route(entity_id, self._route_name(entity_id))

    def on_service_delete(self, service: Service):
        if self.service_routes:
            self.delete_route(self._route_name(service.entity_id))

    def set_env(self, name: str, value):
        self.openshift.environ(self.deployment)[name] = value

    def get_env(self, name: str):
        return self.openshift.environ(self.deployment)[name]

    def add_route(self, url_fragment, name: Optional[str] = None):
        """Adds new route for this apicast"""
        identifier = name or url_fragment
        url = urlparse(self.endpoint % url_fragment)
        self.openshift.routes.expose(name=identifier,
                                     service=self.service_name, hostname=url.hostname)
        self.routes.append(identifier)

    def delete_route(self, identifier):
        """Delete route"""
        if identifier in self.routes and identifier in self.openshift.routes:
            del self.openshift.routes[identifier]
            self.routes.remove(identifier)

    def create(self):
        LOGGER.debug('Deploying new template-based apicast "%s". Template params: "%s"',
                     self.deployment, self.get_app_params())

        self._create_configuration_url_secret()

        self.openshift.new_app(self.template, self.get_app_params())

        # pylint: disable=protected-access
        self.openshift._wait_for_deployment(self.deployment)

    def destroy(self):
        LOGGER.debug('Destroying template-based apicast "%s"...', self.deployment)

        for route in self.routes:
            if route in self.openshift.routes:
                LOGGER.debug('Removing route "%s"...', route)
                del self.openshift.routes[route]

        LOGGER.debug('Deleting service "%s"', self.deployment)
        self.openshift.delete("service", self.deployment)

        LOGGER.debug('Deleting deploymentconfig "%s"', self.deployment)
        self.openshift.delete("deploymentconfig", self.deployment)

        LOGGER.debug('Deleting secret "%s"', self.configuration_url_secret_name)
        self.openshift.delete("secret", self.configuration_url_secret_name)

    def reload(self):
        self.openshift.rollout(self.deployment)

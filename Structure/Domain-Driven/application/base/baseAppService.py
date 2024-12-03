from django.conf import settings
from focus_power.infrastructure.logger.models import AttributeLogger


class BaseAppServiceWithAttributeLogger:
    @property
    def log(self) -> AttributeLogger:
        return settings.GLOBAL_ATTRIBUTE_LOGGER_INSTANCE

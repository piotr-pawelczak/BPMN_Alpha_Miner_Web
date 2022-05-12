from django.db import models
from django.core.validators import FileExtensionValidator

# Create your models here.


class LogFile(models.Model):
    log_file = models.FileField(
        validators=[FileExtensionValidator(allowed_extensions=["csv", "xes"])],
    )


from django.db import models
from django.core.validators import FileExtensionValidator

# Create your models here.


class LogFile(models.Model):
    log_file = models.FileField(
        validators=[FileExtensionValidator(allowed_extensions=["csv", "xes"])],
    )
    activity_column_name = models.CharField(max_length=150, blank=True)
    case_id_column_name = models.CharField(max_length=150, blank=True)
    timestamp_column_name = models.CharField(max_length=150, blank=True)



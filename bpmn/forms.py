from django import forms
from .models import LogFile


class LogForm(forms.ModelForm):

    class Meta:
        model = LogFile
        fields = ['log_file']

        widgets = {
            'log_file': forms.ClearableFileInput(attrs={"id": "file-upload-input"})
        }


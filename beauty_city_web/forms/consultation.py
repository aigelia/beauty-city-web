from django import forms
from django.core.exceptions import ValidationError
from ..models import Consultation


class BaseConsultationForm(forms.ModelForm):
    """Базовый класс формы записи на консультацию с общей валидацией"""

    class Meta:
        model = Consultation
        fields = [
            "client",
            "status",
            "notes",
        ]

    def clean(self):
        """Общая валидация формы"""
        cleaned_data = super().clean()
        return cleaned_data


class ConsultationAdminForm(BaseConsultationForm):
    """Форма записи для админки с выбором времени из списка"""

    class Meta(BaseConsultationForm.Meta):
        fields = BaseConsultationForm.Meta.fields + ["status", "notes"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean_status(self):
        """Валидация статуса консультации"""
        status = self.cleaned_data.get("status")
        if status not in ["pending", "completed"]:
            raise ValidationError("Некорректный статус консультации.")
        return status


class ConsultationForm(BaseConsultationForm):
    """Форма записи для фронтенда"""

    class Meta(BaseConsultationForm.Meta):
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

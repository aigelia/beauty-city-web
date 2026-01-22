from django import forms
from django.core.exceptions import ValidationError
from ..models import PromoCode


class PromoCodeForm(forms.ModelForm):
    class Meta:
        model = PromoCode
        fields = [
            "code",
            "discount_type",
            "discount_value",
            "description",
            "valid_from",
            "valid_to",
            "is_active",
        ]
        widgets = {
            "valid_from": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"}
            ),
            "valid_to": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        valid_from = cleaned_data.get("valid_from")
        valid_to = cleaned_data.get("valid_to")

        if valid_from and valid_to and valid_from >= valid_to:
            raise ValidationError("Дата окончания должна быть позже даты начала")

        return cleaned_data

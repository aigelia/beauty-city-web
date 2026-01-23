from django import forms
from phonenumber_field.formfields import PhoneNumberField
from ..models import Salon


class SalonForm(forms.ModelForm):
    phone = PhoneNumberField(
        region="RU", widget=forms.TextInput(attrs={"placeholder": "+7(999)999-99-99"})
    )

    class Meta:
        model = Salon
        fields = "__all__"

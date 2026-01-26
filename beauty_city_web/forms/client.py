from django import forms
from phonenumber_field.formfields import PhoneNumberField
from ..models import Client


class ClientForm(forms.ModelForm):
    phone = PhoneNumberField(
        region="RU",
        widget=forms.TextInput(attrs={"placeholder": "+7(999)999-99-99"}),
        error_messages={
            'invalid': 'Введите корректный номер телефона (например, 89998887766 или +79998887766).'
        }
    )

    class Meta:
        model = Client
        fields = ["phone", "name", "email"]

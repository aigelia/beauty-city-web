from django import forms
from phonenumber_field.formfields import PhoneNumberField
from ..models import PromoCode


class AppointmentBookingForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(
            attrs={"class": "contacts__form_iunput", "placeholder": "Введите имя"}
        ),
    )

    phone = PhoneNumberField(
        region="RU",
        widget=forms.TextInput(
            attrs={"class": "contacts__form_iunput", "placeholder": "+7(999)999-99-99"}
        ),
        label="Телефон",
    )

    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(
            attrs={
                "class": "contacts__form_iunput",
                "placeholder": "Email (необязательно)",
            }
        ),
    )

    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "contacts__form_textarea",
                "placeholder": "Дополнительные пожелания",
                "rows": 3,
            }
        ),
    )

    promo_code = forms.CharField(
        required=False,
        max_length=50,
        widget=forms.TextInput(
            attrs={
                "class": "contacts__form_iunput",
                "placeholder": "Промокод (если есть)",
            }
        ),
    )

    terms_agreed = forms.BooleanField(
        required=True,
        error_messages={
            "required": "Вы должны согласиться с политикой конфиденциальности"
        },
    )

    def clean(self):
        cleaned_data = super().clean()

        promo_code = cleaned_data.get("promo_code")
        if promo_code:
            try:
                promo = PromoCode.objects.get(code=promo_code, is_active=True)
                if not promo.is_valid():
                    self.add_error("promo_code", "Промокод недействителен")
            except PromoCode.DoesNotExist:
                self.add_error("promo_code", "Промокод не найден")

        return cleaned_data

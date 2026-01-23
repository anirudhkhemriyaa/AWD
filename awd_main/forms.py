from django import forms
from django.contrib.auth.forms import UserCreationForm
from Data_entry.models import CustomUser

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control bg-light text-dark border-secondary",
                "placeholder": "Email address"
            }
        )
    )

    class Meta:
        model = CustomUser
        fields = (
            "Name_of_Company",
            "Name_of_Encharge",
            "phone",
            "Sector",
            "company_size",
            "email",
            "username",
            "password1",
            "password2",
        )

        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": "form-control bg-light text-dark border-secondary",
                    "placeholder": "Username"
                }
            ),
        }

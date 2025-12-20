from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

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
        model = User
        fields = ("email", "username", "password1", "password2")

        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": "form-control bg-light text-dark border-secondary",
                    "placeholder": "Username"
                }
            ),
            "password1": forms.PasswordInput(
                attrs={
                    "class": "form-control bg-light text-dark border-secondary",
                    "placeholder": "Password"
                }
            ),
            "password2": forms.PasswordInput(
                attrs={
                    "class": "form-control bg-light text-dark border-secondary",
                    "placeholder": "Confirm password"
                }
            ),
        }

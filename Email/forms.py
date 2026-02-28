from django import forms
from .models import Email

class Email_form(forms.ModelForm):

    class Meta:
        model = Email
        exclude = ["company"]

        widgets = {
            # Email list / recipients
            "email_list": forms.Select(
                attrs={
                    "class": "form-select bg-dark text-light border-secondary text-center"
                }
            ),

            # Subject
            "subject": forms.TextInput(
                attrs={
                    "class": "form-control bg-dark text-light border-secondary",
                    "placeholder": "Email subject"
                }
            ),

            # Message body (CKEditor will replace this)
            "body": forms.Textarea(
                attrs={
                    "class": "form-control bg-dark text-light border-secondary",
                    "rows": 6
                }
            ),

            # Attachment
            "attachment": forms.ClearableFileInput(
                attrs={
                    "class": "form-control bg-dark text-light border-secondary"
                }
            ),
        }

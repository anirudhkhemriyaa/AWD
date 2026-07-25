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
                    "class": "form-select"
                }
            ),

            # Subject
            "subject": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter email subject..."
                }
            ),

            # Message body (CKEditor will replace this)
            "body": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6
                }
            ),

            # Attachment
            "attachment": forms.ClearableFileInput(
                attrs={
                    "class": "form-control"
                }
            ),
        }


from django import forms
from .models import Email

class Email_form(forms.ModelForm):

    class Meta:
        model = Email
        fields = ('__all__')
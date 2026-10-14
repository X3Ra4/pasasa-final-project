from django import forms
from django.contrib.auth.forms import PasswordChangeForm

from .models import User


class AccountProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        avatar_widget = self.fields["avatar"].widget
        avatar_widget.template_name = "widgets/account_avatar_input.html"
        avatar_widget.attrs.update(
            {
                "class": "account-file-input",
                "accept": "image/*",
            }
        )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "avatar", "bio")
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 5}),
        }


class AccountPasswordForm(PasswordChangeForm):
    old_password = forms.CharField(widget=forms.PasswordInput(render_value=False))
    new_password1 = forms.CharField(widget=forms.PasswordInput(render_value=False))
    new_password2 = forms.CharField(widget=forms.PasswordInput(render_value=False))

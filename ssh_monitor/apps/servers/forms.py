from django import forms

from apps.core.encryption import encrypt_credential
from apps.servers.models import AuthType, Server


class ServerForm(forms.ModelForm):
    credential_input = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text="Password for password auth, or private key text for key-file auth.",
    )

    class Meta:
        model = Server
        fields = [
            "name",
            "host",
            "port",
            "ssh_username",
            "auth_type",
            "check_interval_minutes",
            "monitoring_enabled",
        ]
        widgets = {
            "port": forms.NumberInput(attrs={"placeholder": "22"}),
            "check_interval_minutes": forms.NumberInput(attrs={"min": 1, "max": 1440}),
        }

    def clean(self):
        cleaned_data = super().clean()
        auth_type = cleaned_data.get("auth_type")
        credential_input = cleaned_data.get("credential_input", "").strip()
        is_edit = bool(self.instance and self.instance.pk)
        previous_auth_type = self.instance.auth_type if is_edit else None

        if auth_type in (AuthType.PASSWORD, AuthType.KEY_FILE, AuthType.GENERATED_KEY) and not credential_input:
            if not is_edit or auth_type != previous_auth_type:
                self.add_error(
                    "credential_input",
                    "Credential input is required for selected authentication type.",
                )
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        credential_input = self.cleaned_data.get("credential_input", "")
        if credential_input:
            instance.credentials_encrypted = encrypt_credential(credential_input)
        if commit:
            instance.save()
        return instance

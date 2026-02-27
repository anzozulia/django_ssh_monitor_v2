from django import forms


class TelegramConfigForm(forms.Form):
    bot_token = forms.CharField(
        max_length=255,
        label="Bot Token",
        widget=forms.TextInput(attrs={"placeholder": "123456789:AA..."}),
    )
    chat_id = forms.CharField(
        max_length=255,
        label="Chat / Group ID",
        widget=forms.TextInput(attrs={"placeholder": "-1001234567890"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = (
                "h-11 w-full rounded-lg border border-gray-300 bg-transparent px-4 py-2.5 "
                "text-theme-sm text-gray-900 focus:border-brand-300 focus:ring-3 "
                "focus:ring-brand-500/10 focus:outline-hidden"
            )

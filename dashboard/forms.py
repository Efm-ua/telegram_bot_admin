from django import forms

class MessageForm(forms.Form):
    message_text = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5}),
        label="Текст повідомлення"
    )
    photo_url = forms.URLField(
        required=False,
        label="URL фото (необов'язково)"
    )
    add_buttons = forms.BooleanField(
        required=False,
        label="Додати кнопки"
    )
    button_text = forms.CharField(
        required=False,
        label="Текст кнопки"
    )
    button_url = forms.URLField(
        required=False,
        label="URL кнопки"
    )
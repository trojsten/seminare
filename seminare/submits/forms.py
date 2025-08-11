from django import forms


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        return result


class FileFieldForm(forms.Form):
    files = MultipleFileField()

    def clean(self, *args, **kwargs):
        data = super().clean()
        if data is None:
            raise forms.ValidationError("Nahraj aspoň jeden súbor.")

        files = data.get("files", [])
        if len(files) <= 0:
            raise forms.ValidationError({files: "Nahraj aspoň jeden súbor."})

        if len(files) > 1 and not all(
            f.name.lower().endswith((".jpg", ".jpeg", ".png")) for f in files
        ):
            raise forms.ValidationError(
                {
                    files: "Možeš odovzdať iba jeden PDF súbor, alebo viacero obrázkov (.jpg, .jpeg, .png)"
                }
            )

        return data


class JudgeSubmitForm(forms.Form):
    program = forms.FileField()


class TextSubmitForm(forms.Form):
    text = forms.CharField()

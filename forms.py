from django import forms

class FileUploadForm(forms.Form):
    DREAMTYPES = (
        ("default", "Strange"),
        ("inception_3b/5x5_reduce", "Impressionist"),
    )

    picture = forms.FileField(label="picture", required=True, widget=forms.FileInput(attrs={"class":"form-control", "required":"true"}))
    dreamtype = forms.ChoiceField(choices=DREAMTYPES, label="dreamtype", required=True, widget=forms.Select(attrs={"class":"form-control"}))

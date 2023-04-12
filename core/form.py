from django import forms



class VideoForm(forms.Form):
    # video = forms.FileField()
    # image = forms.ImageField()

    video = forms.CharField(required=True)
    image = forms.CharField(required=False)
    id = forms.IntegerField(required=False)
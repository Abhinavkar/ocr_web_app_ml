from django import forms

class DocumentForm(forms.Form):
    pdf = forms.FileField()

class ImageForm(forms.Form):
    image = forms.ImageField()

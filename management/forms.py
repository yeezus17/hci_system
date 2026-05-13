from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Annonce, Profile

# Custom widget to allow multiple file uploads
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True  # This is the key flag Django checks

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        # Handle multiple files
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class AnnonceForm(forms.ModelForm):
    media_files = MultipleFileField(
        widget=MultipleFileInput(attrs={
            'class': 'input-field w-full px-5 py-4 rounded-2xl text-sm',
            'accept': 'image/*,video/*'
        }),
        required=False,
        label="Photos & Vidéos"
    )

    class Meta:
        model = Annonce
        fields = [
            'titre', 'type_transaction', 'type_bien',
            'ville', 'prix', 'description', 'latitude', 'longitude'
        ]
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'input-field w-full px-5 py-4 rounded-2xl text-sm', 'placeholder': 'Ex: Magnifique Villa'}),
            'type_transaction': forms.Select(attrs={'class': 'input-field w-full px-5 py-4 rounded-2xl text-sm cursor-pointer'}),
            'type_bien': forms.Select(attrs={'class': 'input-field w-full px-5 py-4 rounded-2xl text-sm cursor-pointer'}),
            'ville': forms.TextInput(attrs={'class': 'input-field w-full px-5 py-4 rounded-2xl text-sm', 'placeholder': 'Ville'}),
            'prix': forms.NumberInput(attrs={'class': 'input-field w-full px-5 py-4 rounded-2xl text-sm', 'placeholder': 'Prix (DH)'}),
            'description': forms.Textarea(attrs={'class': 'input-field w-full px-5 py-4 rounded-2xl text-sm h-32', 'placeholder': 'Description...'}),
            'latitude': forms.HiddenInput(attrs={'id': 'lat-input'}),
            'longitude': forms.HiddenInput(attrs={'id': 'lng-input'}),
        }



class HCISignupForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'field-input', 'placeholder': 'Prénom'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'field-input', 'placeholder': 'Nom'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'field-input', 'placeholder': 'Email'}))
    phone = forms.CharField(max_length=20, required=True, widget=forms.TextInput(attrs={'class': 'field-input', 'placeholder': 'Téléphone'}))

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError("Cette adresse email est déjà enregistrée. Veuillez vous connecter.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"] 
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        
        if commit:
            user.save()
            profile, created = Profile.objects.get_or_create(user=user)
            profile.phone_number = self.cleaned_data["phone"]
            profile.save()
        return user
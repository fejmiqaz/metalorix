import warnings
from io import BytesIO
from PIL import Image, ImageOps, UnidentifiedImageError
from django import forms
from .models import Idea


class MultipleInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class ReferenceImages(forms.FileField):
    widget = MultipleInput

    def clean(self, data, initial=None):
        files = data if isinstance(data, (list, tuple)) else ([data] if data else [])
        if len(files) > 3:
            raise forms.ValidationError('Please choose at most 3 images.')
        result = []
        for upload in files:
            if upload.size > 2 * 1024 * 1024:
                raise forms.ValidationError('Each image must be 2 MB or smaller.')
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter('error', Image.DecompressionBombWarning)
                    with Image.open(upload) as source:
                        if source.format not in {'JPEG', 'PNG', 'WEBP'} or source.width * source.height > 16000000:
                            raise ValueError()
                        clean = ImageOps.exif_transpose(source).convert('RGB')
                        clean.thumbnail((1600, 1600))
                        output = BytesIO()
                        clean.save(output, 'JPEG', quality=85)
                        result.append(output.getvalue())
            except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombWarning, Image.DecompressionBombError):
                raise forms.ValidationError('Use valid JPG, PNG, or WebP images, up to 16 megapixels.')
        return result


class IdeaForm(forms.ModelForm):
    sender_name = forms.CharField(max_length=120, label='Your name', widget=forms.TextInput(attrs={'autocomplete': 'name', 'placeholder': 'Your name'}))
    sender_email = forms.EmailField(label='Your email', help_text='Private. Used to group your ideas together; not shown on the website.',
                                   widget=forms.EmailInput(attrs={'autocomplete': 'email', 'placeholder': 'you@example.com'}))
    field_order = ['sender_name', 'sender_email', 'title', 'song', 'description', 'images', 'website']
    images = ReferenceImages(required=False, help_text='Optional · up to 3 JPG, PNG or WebP images · 2 MB each',
                             widget=MultipleInput(attrs={'accept': 'image/jpeg,image/png,image/webp'}))
    website = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = Idea
        fields = ['title', 'song', 'description']
        widgets = {'title': forms.TextInput(attrs={'placeholder': 'Give your idea a name'}),
                   'song': forms.TextInput(attrs={'placeholder': 'Song title — artist, or a link'}),
                   'description': forms.Textarea(attrs={'rows': 5, 'placeholder': 'What does it feel like? A memory, a color, a late-night thought…'})}

    def clean_website(self):
        if self.cleaned_data['website']:
            raise forms.ValidationError('Unable to submit this idea.')
        return ''

    def clean_sender_email(self):
        return self.cleaned_data['sender_email'].strip().lower()

from django import forms
from django.conf import settings

class ThumbModelForm(forms.ModelForm):
    """ Wrapper around ModelForm, overwrites the save method so that calling 
    form.save() also saves the images """
    class Meta:
        abstract = True
        
	def save(self, *args, **kwargs):
		for key in self.files:
			setattr(self.instance, key, self.files[key])
		return super(ThumbModelForm, self).save(*args, **kwargs)

class ThumbForm(forms.Form):
    """ Wrapper around Form, overwrites the save method so that calling 
    form.save() also saves the images """
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
    for key in self.files:
        setattr(self.instance, key, self.files[key])
    return super(ThumbModelForm, self).save(*args, **kwargs)

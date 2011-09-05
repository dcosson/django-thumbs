django-thumbs
9/5/2011

### Significant additions in v0.2, makes django-thumbs easier to use and maintains full backward-compatibility

This is a fork of "github.com/Level-Up/django-thumbs.git".  See README_ORIGINAL for the original README file.

### Features
+ Easy to integrate into your code - just an ImageField with a few extra (optional) arguments to control thumbnailing
+ Works perfectly with any StorageBackend
+ Generates thumbnails after image is uploaded into memory
+ Deletes thumbnails when the image file is deleted

### New in v0.2
+ Easier (read: more loosely coupled) access to the various thumbnail sizes - give each size a name and access its url by name (i.e. obj.picture.get_image_url("tiny") instead of obj.picture.url_80x80).
+ Specify a default url (as an argument to the model field or in settings.DEFAULT_IMAGE_URL) to be used if no image is uploaded
+ Option to specify a "fullsize" image that maintains original aspect ratio but is scaled down to some maximum width or height. 
+ Regenerate thumbnails at any time without having to re-upload the original image

### Optional shortcuts:
+ Thin wrappers around forms.Form and forms.ModelForm classes so calling form.save() on a bound form will look through request.FILES and save the images/files.
+ add "thumbs" to your INSTALLED_APPS for template tags that return the correct image url 



### Installation: 
git clone and run ./setup.py install or install with pip, passing it the 

### Note:


Version 0.1I added a simple setup.py file so it can be installed as a package (with pip).  Also added the default South introspection rules, so South 0.7+ won't complain about migrating an ImageWithThumbsField, and added a few attributes that are used by the Model wrapper described below.


To make for less boilerplate code when working with django-thumbs and help keep the presentation logic (size in pixels of each thumbnail created) separate, I have created Model and ModelForm wrapper classes.  

ModelThumb is the same as django.db.models.Model but adds a

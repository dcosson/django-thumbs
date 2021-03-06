django-thumbs
9/5/2011

##Significant additions in v0.2, makes django-thumbs easier to use and maintains full backward-compatibility

This is a fork of [github.com/Level-Up/django-thumbs.git](http://github.com/Level-Up/django-thumbs.git).  See README_ORIGINAL for the original readme file. I've tested on Django 1.2 and 1.3, but feel free to try it on 1.0+

###Features
+ Easy to integrate into your code - just an ImageField with a few extra (optional) arguments to control thumbnailing
+ Works perfectly with any StorageBackend
+ Generates thumbnails after image is uploaded into memory
+ Deletes thumbnails when the image file is deleted

###Added in forked version
+ Simpler (more loosely coupled) access to the various thumbnail sizes - give each size a name and access its url by name (i.e. `obj.picture.get_image_url("tiny")` instead of `obj.picture.url_80x80`).
+ Specify a default url (as an argument to the model field or in `settings.DEFAULT_IMAGE_URL`) to be used if no field is empty
+ Option to specify a "fullsize" image that maintains original aspect ratio but is scaled down to some maximum width or height. 
+ Regenerate thumbnails at any time without having to re-upload the original image
+ Packaged as a python module (install with setup.py or pip, put in requirements.txt file, etc.)
+ South introspection rules (so south >= 0.7 doesn't complain about migrating)

###Optional shortcuts
+ wrappers around `forms.Form` and `forms.ModelForm` classes so calling `form.save()` on a bound form will look through request.FILES and save the images/files.
+ template tags for displaying your images

###Installation and setup

1. git clone and run `./setup.py install` or install with `pip git+git://github.com/dcosson/django-thumbs` 
2. add `DEFAULT_IMAGE_URL` to settings (optional) as the url to be used if ImageField is blank
3. add "thumbs"  to `INSTALLED_APPS` (optional) to use the image and image_url template tags 

###License

[New BSD License](http://www.opensource.org/licenses/bsd-license.php)

### Examples:

models.py

    from django.db import models
    from thumbs import ImageWithThumbsField
    from django.conf import settings
    
    fs = FileSystemStorage(location=settings.MEDIA_URL) # assume MEDIA_URL is /media/
    
    class Person(models.Model):
        photo = ImageWithThumbsField(storage = fs, upload_to = 'person_images', 
                                     sizes = ((125,125), (200,200)),
                                     size_names = ("small", "medium"),
                                     fullsize = (500,0),
                                     default_image = settings.STATIC_URL + "images/person_silhouette.png",
                                     )
    
When someone uploads a photo, this will create two square (cropped) thumbnails that you can access as "small" and "medium" as well as an image whose width is scaled down to 500px (i.e. if it was 2000 x 3200 to begin with, the "full" version will be 500 x 800).  

The reason for the full-sized attribute is that your users are probably uploading enormous photos straight from their 15 mega-pixel digital cameras.  In your css you're probably defining a max-width and/or max-height anyway, so there's no reason to waste bandwidth and increase page-load times by using these original images directly.  The original is still saved, though, so you can always regenerate your "fullsize" and thumbnails later if your site layout changes (of course, it has to load the original picture into memory to give it to PIL to recalculate these, so it will take a while if you have a lot of objects with images). 
    
Accessing:

    >>> p = Person.objects.all()[0] # get the first person added
    >>> print p.photo.name
    image_name.jpg
    >>> print p.photo.get_image_url("small")
    /media/person_images/image_name.125x125.jpg
    >>> print p.photo.get_image_url("full")
    /media/person_images/image_name.500x0.full.jpg
    >>> print p.photo.get_image_url("original")
    /media/person_images/image_name.jpg

Regenerating the thumbs - say, if you changed "small" to (100,100)

    >>> p.photo.regenerate_thumbs()
    >>>
    >>> p.photo.get_image_url("small")
    /media/person_images/image_name.100x100.jpg
  
If photo is empty:   

    >>> p.photo = None
    >>> p.save()
    >>> print p.get_image_url("small")
    /static/images/person_silhouette.png

Template tags (put thumbs into installed apps for the tags to get registered):

`{% load thumb_tags %}`

`{% image_url p.photo "full" %}`  generates:  `/media/person_images/image_name.500x0.full.jpg`

`{% image p.photo "full" "user uploaded photo" %}` generates: `<img src="/media/person_images/image_name.500x0.full.jpg" alt="user uploaded photo" />`

###Uninstall

At any time you can go back and use `ImageField` again without altering the database or anything else. 
Just replace `ImageWithThumbsField` with `ImageField` again and make sure you delete the `sizes`, `size_names`, `fullsize`, and `default_image` attributes. 
Everything will work the same way it worked before using django-thumbs (remember to delete generated 
thumbnails in the case you don't want to have them anymore).
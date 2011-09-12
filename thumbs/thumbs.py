# -*- encoding: utf-8 -*-
"""
django-thumbs by Antonio Melé
http://django.es
"""
from django.db.models import ImageField
from django.db.models.fields.files import ImageFieldFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image
from django.core.files.base import ContentFile
from django.conf import settings
import cStringIO
#South introspection rules to deal with thumbs:
from south.modelsinspector import add_introspection_rules
add_introspection_rules([], [__name__ + r'.ImageWithThumbsField'])

VERSION = 0.2

def generate_thumb(img, thumb_size, format):
    """
    Generates a thumbnail image and returns a ContentFile object with the thumbnail
    
    Parameters:
    ===========
    img         File object
    
    thumb_size  desired thumbnail size, ie: (200,120)
    
    format      format of the original image ('jpeg','gif','png',...)
                (this format will be used for the generated thumbnail, too)
    """
    
    img.seek(0) # see http://code.djangoproject.com/ticket/8222 for details
    image = Image.open(img)
    
    # Convert to RGB if necessary
    if image.mode not in ('L', 'RGB'):
        image = image.convert('RGB')
        
    # get size
    thumb_w, thumb_h = thumb_size
    # If you want to generate a square thumbnail
    if thumb_w == thumb_h:
        # quad
        xsize, ysize = image.size
        # get minimum size
        minsize = min(xsize,ysize)
        # largest square possible in the image
        xnewsize = (xsize-minsize)/2
        ynewsize = (ysize-minsize)/2
        # crop it
        image2 = image.crop((xnewsize, ynewsize, xsize-xnewsize, ysize-ynewsize))
        # load is necessary after crop                
        image2.load()
        # thumbnail of the cropped image (with ANTIALIAS to make it look better)
        image2.thumbnail(thumb_size, Image.ANTIALIAS)
    else:
        # not quad
        image2 = image
        image2.thumbnail(thumb_size, Image.ANTIALIAS)
    
    io = cStringIO.StringIO()
    # PNG and GIF are the same, JPG is JPEG
    if format.upper()=='JPG':
        format = 'JPEG'
    
    image2.save(io, format)
    return ContentFile(io.getvalue())    

def generate_resized(img, max_dimensions, format):
    """ 
    Creates a resized copy of the image at the same aspect ratio (i.e. without cropping or skewing).
    
    Note that the new image will *NOT* be equal to max_dimensions in the general case (if that's what
    you want, use the generate_thumb() function to crop to a specified size).  One dimension will be 
    equal to its value given in max_dimensions, the other will be larger than its corresponding 
    max_dimension value.
	
    Ex: You are setting the max-width of a user's profile picture on your site to 400px with no limit 
    on the height.  Set max_dimensions = (400,0)
    
    The point of this is to shrink the image that you use as the full-sized version of the picture. If
    your site takes user-uploaded photos, users will upload huge pictures without thinking about it. 
    No reason to waste bandwidth and increase page-load times by displaying with these original images
    directly.  The original is still saved, so you can always regenerate your resized and thumbnailed 
    versions later.
    """
    img.seek(0) # see http://code.djangoproject.com/ticket/8222 for details
    image = Image.open(img)
    
    # Convert to RGB if necessary
    if image.mode not in ('L', 'RGB'):
        image = image.convert('RGB')
        
    # get size limits
    max_w = max_dimensions[0] or 1 #change 0px to 1 px to prevent division by 0 error
    max_h = max_dimensions[1] or 1
    w, h = image.size
    if float(w) / max_w <= float(h) / max_h:
        #set width to limit, height will be smaller than its limit
        new_w = max_w
        new_h = new_w * h / w #maintain aspect ratio
    else:
        new_h = max_h
        new_w = new_h * w / h
    #resize image
    print "new width: %d, new height: %d" % (new_w, new_h) #for debugging
    image2 = image.resize((new_w, new_h), Image.ANTIALIAS)

    io = cStringIO.StringIO()
    # PNG and GIF are the same, JPG is JPEG
    if format.upper()=='JPG':
        format = 'JPEG'
    
    image2.save(io, format)
    return ContentFile(io.getvalue())    


	
class ImageWithThumbsFieldFile(ImageFieldFile):
    """
    See ImageWithThumbsField for usage example
    """
    def __init__(self, *args, **kwargs):
        super(ImageWithThumbsFieldFile, self).__init__(*args, **kwargs)
        self.sizes = self.field.sizes
        # Extra attributes, only used in the ThumbModels class:
        self.size_names = self.field.size_names
        self.fullsize = self.field.fullsize
        self.default_image = self.field.default_image
        
        if self.sizes:
            def get_size(self, size):
                if not self:
                    return ''
                else:
                    split = self.url.rsplit('.',1)
                    (w,h) = size
                    thumb_url = '%s.%sx%s.%s' % (split[0],w,h,split[1])
                    return thumb_url
     
            for size in self.sizes:
                (w,h) = size
                setattr(self, 'url_%sx%s' % (w,h), get_size(self, size))
                
        if self.fullsize:
		# scale down the "full size" version of the image, subject to min width & height
            def get_fullsize(self, size):
                if not self:
                    return ''
                else:
                    split = self.url.rsplit('.',1)
                    (w,h) = size
                    thumb_url = '%s.%sx%s.full.%s' % (split[0],w,h,split[1])
                    return thumb_url

            setattr(self, 'url_full', get_fullsize(self, self.fullsize)) 
    
    def get_image_url(self, size_name="full"):
        """ Wrapper to get different sized thumbs by a name (not tied to exact size) """
        #default url - try self.default_image, then DEFAULT_IMAGE_URL setting, then empty string
        if self.default_image:
            url = self.default_image
        elif hasattr(settings, "DEFAULT_IMAGE_URL"):
            url = settings.DEFAULT_IMAGE_URL
        else:
            url = ""
        
        if size_name == "original":
            url = self.url
            
        elif self.fullsize and (size_name == "full" or size_name == "fullsize"):
            #(w,h) = self.fullsize #fullsize attribute doesn't have size
            url = getattr(self, 'url_full')

        if self.sizes and self.size_names and size_name in self.size_names:
            (w,h) = self.sizes[ self.size_names.index(size_name) ]
            url = getattr(self, 'url_%sx%s' % (w,h))
        return url
    
    def _save_thumbs(self, content):
        """ Save thumbnailed and resized images without calling the save() method
               inherited from ImageField (used for regenerating thumbs) """
        
        if self.sizes:
            for size in self.sizes:
                (w,h) = size
                split = self.name.rsplit('.',1)
                thumb_name = '%s.%sx%s.%s' % (split[0],w,h,split[1])
                
                # you can use another thumbnailing function if you like
                thumb_content = generate_thumb(content, size, split[1])
                
                thumb_name_ = self.storage.save(thumb_name, thumb_content)        
                
                if not thumb_name == thumb_name_:
                    raise ValueError('There is already a file named %s' % thumb_name)
					
        if self.fullsize:
            for size in tuple( [self.fullsize,] ):
                # work with a tuple - in the future, might want to allow multiple resize options not just a single fullsize
                (w,h) = size
                split = self.name.rsplit('.', 1)
                fullsize_name = '%s.%sx%s.full.%s' % (split[0],w,h,split[1])
                fullsize_content = generate_resized(content, size, split[1])
                
                fullsize_name_ = self.storage.save(fullsize_name, fullsize_content)
                
                if not fullsize_name == fullsize_name_:
                    raise ValueError('There is already a file named %s' % fullsize_name)
    
    def save(self, name, content, save=True):
        super(ImageWithThumbsFieldFile, self).save(name, content, save)
        self._save_thumbs( content )
    
    def _delete_thumbs(self):
        """ Useful to clean up your files if you're about to change the size of your thumbs 
        """
        if self.sizes:
            for size in self.sizes:
                (w,h) = size
                split = self.name.rsplit('.',1)
                thumb_name = '%s.%sx%s.%s' % (split[0],w,h,split[1])
                try:
                    self.storage.delete(thumb_name)
                except:
                    pass
        if self.fullsize:
            for size in tuple( [self.fullsize,] ):
                (w,h) = size
                split = self.name.rsplit('.',1)
                fullsize_name = '%s.%sx%s.full.%s' % (split[0],w,h,split[1])
                try:
                    self.storage.delete(fullsize_name)
                except:
                    pass
    
    def delete(self, save=True):
        super(ImageWithThumbsFieldFile, self).delete(save)
        self._delete_thumbs()
				
    def regenerate_thumbs(self):
        # -- Delete existing thumbs and resized images
        #   Note: (if you have changed the sizes, it won't know to delete the thumbs of the old sizes.  #          call _delete_thumbs before changing size to clean those up
        self._delete_thumbs()
        
        # -- Create new thumbs and resized images
        img = Image.open(self)
        img.seek(0) # you would think it's already at the beginning, but everyone else is doing it
        # set image format:
        format = self.name.rsplit(".", 1)[1]
        if format.upper() == "JPG":
            format = "JPEG"
        # Load into memory for PIL to use
        size = settings.FILE_UPLOAD_MAX_MEMORY_SIZE
        io = cStringIO.StringIO()
        img.save(io, format)
        io.seek(0) # here we do need it
        pic = InMemoryUploadedFile(io, "", self.name, "image", size, "utf-8")
        pic.DEFAULT_CHUNK_SIZE = size #otherwise biggest image it will handle is 64 kB
        self._save_thumbs(pic)
                        
class ImageWithThumbsField(ImageField):
    attr_class = ImageWithThumbsFieldFile
    """
    Usage example:
    ==============
    photo = ImageWithThumbsField(upload_to='images', sizes=((125,125),(300,200),)
    
    To retrieve image URL, exactly the same way as with ImageField:
        my_object.photo.url
    To retrieve thumbnails URL's just add the size to it:
        my_object.photo.url_125x125
        my_object.photo.url_300x200
    
    Note: The 'sizes' attribute is not required. If you don't provide it 
    ImageWithThumbsField will act as a normal ImageField
   
    The 'size_names' attribute is also not required and does not affect creation 
    of the thumbnails, it is for accessing them through the ThumbModels class.
 
    How it works:
    =============
    For each size in the 'sizes' atribute of the field it generates a 
    thumbnail with that size and stores it following this format:
    
    available_filename.[width]x[height].extension

    Where 'available_filename' is the available filename returned by the storage
    backend for saving the original file.
    
    Following the usage example above: For storing a file called "photo.jpg" it saves:
    photo.jpg          (original file)
    photo.125x125.jpg  (first thumbnail)
    photo.300x200.jpg  (second thumbnail)
    
    With the default storage backend if photo.jpg already exists it will use these filenames:
    photo_.jpg
    photo_.125x125.jpg
    photo_.300x200.jpg
    
    Note: django-thumbs assumes that if filename "any_filename.jpg" is available 
    filenames with this format "any_filename.[width]x[height].jpg" will be available, too.
    
    To do:
    ======
    Add method to regenerate thubmnails
    """
    def __init__(self, verbose_name=None, name=None, width_field=None, height_field=None, sizes=None, size_names=None, fullsize=None, default_image="", **kwargs):
        self.verbose_name=verbose_name
        self.name=name
        self.width_field=width_field
        self.height_field=height_field
        self.sizes = sizes
        self.size_names = size_names
        self.fullsize = fullsize
        self.default_image = default_image
        super(ImageField, self).__init__(**kwargs)
		
#Add the South Introspection rules for the ImageWithThumbsField
add_introspection_rules(
	[(
		(ImageWithThumbsField,),
		[],
		{
			"verbose_name": ["verbose_name", {"default": None}],
			"name": ["name", {"default": None}],
			"width_field": ["width_field", {"default": None}],
			"height_field": ["height_field", {"default": None}],
			"sizes": ["sizes", {"default": None}],
            "size_names": ["size_names", {"default": None}],
            "fullsize": ["fullsize", {"default": None}],
            "default_image": ["default_image", {"default": ""}],
		}
	)],
	["thumbs\.ImageWithThumbsField"]
)
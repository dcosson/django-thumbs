from django import template
register = template.Library()

@register.simple_tag
def image_url(instance, image_size):
    """ Usage:
    {% load thumbmodel_tags %}
    {% image_url item.picture "tiny" %}

    This will return the thumbnail of item.picture in the size associated with "tiny"
    """
    if hasattr(instance, "get_image_url"):
        url = instance.get_image_url(image_size)
    else:
        raise AttributeError("First argument to image_url tag should be an " +
                            "instance of ImageWithThumbsField")
    return url

@register.simple_tag
def image(instance, image_size, alt_text, **args):
    url = image_url(instance, image_size)
    return "<img src=%s alt=%s />" % (url, alt_text,)
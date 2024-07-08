from django_cleanup.signals import cleanup_pre_delete
from easy_thumbnails.files import get_thumbnailer


def easy_delete(**kwargs):
    print("Deleting thumbnails")
    file = kwargs["file"]
    thumbnailer = get_thumbnailer(file)
    thumbnailer.delete_thumbnails()
    print(f"Deleted thumbnails for {file}")


cleanup_pre_delete.connect(easy_delete)

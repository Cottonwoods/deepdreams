from deepdreams.models import Picture
from dreams import *

from celery import current_task
from celery import shared_task

@shared_task
def dreamtask(pic_id):
    picture = Picture.objects.get(id=pic_id)
    dreamtype = picture.dreamtype
    img = PIL.Image.open(picture.pic)
    img.load()
    mode = img.mode
    img = np.float32(img)
    if dreamtype == "default":
        f = showimg(deepdream(current_task.request.id, net, img), mode)
    else:
        f = showimg(deepdream(current_task.request.id, net, img, end=dreamtype), mode)
    picture.dream.save(picture.pic.name, f)
    return pic_id

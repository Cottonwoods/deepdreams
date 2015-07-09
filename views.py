from django.shortcuts import render
from django.http import HttpResponse
import json

from deepdreams.forms import FileUploadForm
from deepdreams.models import Picture
from dreams import *

# Create your views here.
def index(req):
    #img = np.float32(PIL.Image.open('sky1024px.jpg'))
    form = FileUploadForm()
    return render(req, "deepdreams/index.html", {"form": form})

def begindream(req):
    if req.method == "POST":
        form = FileUploadForm(data=req.POST, files=req.FILES)
        picture_response = {}
        if form.is_valid() and req.FILES and req.FILES["picture"]:
            picture = Picture(pic=req.FILES["picture"])
            picture.save()
            dreamtype = req.POST["dreamtype"]
            img = PIL.Image.open(picture.pic)
            img.load()
            mode = img.mode
            img = np.float32(img)
            if dreamtype == "default":
                f = showimg(deepdream(net, img), mode)
            else:
                f = showimg(deepdream(net, img, end=dreamtype), mode)
            dream = Picture()
            dream.pic.save(picture.pic.name, f);
            picture_response["dream_path"] = dream.pic.name
            picture_response["pic_path"] = picture.pic.name
            picture_response["dreamtype"] = req.POST["dreamtype"]
        return HttpResponse(
            json.dumps(picture_response),
            content_type="application/json"
        )
    else:
        return HttpResponse(
            json.dumps({"null": "null"}),
            content_type="application/json"
        )

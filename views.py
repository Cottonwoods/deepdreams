from django.shortcuts import render
from django.http import HttpResponse
from celery.result import AsyncResult
import json

from deepdreams.forms import FileUploadForm
from deepdreams.models import Picture
from deepdreams.tasks import dreamtask
from dreams import *

# Create your views here.
def index(req):
    #img = np.float32(PIL.Image.open('sky1024px.jpg'))
    form = FileUploadForm()
    return render(req, "deepdreams/index.html", {"form": form})

def checkdream(req):
    if req.method == "GET":
        task_id = req.GET["task_id"]
        task = AsyncResult(task_id)
        if task.state == "SUCCESS":
            picture = Picture.objects.get(id=task.result)
            picture_response = {}
            picture_response["pic_path"] = picture.pic.name
            picture_response["dream_path"] = picture.dream.name
            return HttpResponse(
                json.dumps(picture_response),
                content_type="application/json"
            )
        if task.state == "PROGRESS":
            return HttpResponse(
                json.dumps(task.info),
                content_type="application/json",
                status=202
            )
        return HttpResponse(
            json.dumps({"progress": 5}),
            content_type="application/json",
            status=202
        )

def begindream(req):
    if req.method == "POST":
        form = FileUploadForm(data=req.POST, files=req.FILES)
        picture_response = {}
        if form.is_valid() and req.FILES and req.FILES["picture"]:
            picture = Picture(pic=req.FILES["picture"])
            picture.dreamtype = req.POST["dreamtype"]
            picture.save()
            task_id = dreamtask.delay(picture.id).id
            return HttpResponse(
                json.dumps({"task_id": task_id}),
                content_type="application/json"
            )
    return HttpResponse(status=204)

# Add caffe to pythonpath
import sys
sys.path.insert(0, "/home/django/caffe/python")

# Dependences
from django.core.files.base import ContentFile
from cStringIO import StringIO
import numpy as np
import scipy.ndimage as nd
import PIL.Image
from google.protobuf import text_format
import caffe

from celery import current_task

def showimg(a, mode, fmt='png'):
    a = np.uint8(np.clip(a, 0, 255))
    try:
        try:
            im = PIL.Image.fromarray(a)
        except ValueError:
            raise
        try:
            im = PIL.Image.fromarray(a, mode)
        except ValueError:
            raise
        try:
            im = PIL.Image.fromarray(a, 'RGB')
        except ValueError:
            raise
        try:
            im = PIL.Image.fromarray(a, 'RGBA')
        except ValueError:
            raise
    except ValueError:
        pass
    im_io = StringIO()
    im.save(im_io, fmt)
    im_file = ContentFile(im_io.getvalue())
    return im_file

# Loading DNN model
model_path = '/home/django/caffe/models/bvlc_googlenet/' # substitute your path here
net_fn   = model_path + 'deploy.prototxt'
param_fn = model_path + 'bvlc_googlenet.caffemodel'

# Patching model to be able to compute gradients.
# Note that you can also manually add "force_backward: true" line to "deploy.prototxt".
model = caffe.io.caffe_pb2.NetParameter()
text_format.Merge(open(net_fn).read(), model)
model.force_backward = True
open('tmp.prototxt', 'w').write(str(model))

net = caffe.Classifier('tmp.prototxt', param_fn,
                       mean = np.float32([104.0, 116.0, 122.0]), # ImageNet mean, training set dependent
                       channel_swap = (2,1,0)) # the reference model has channels in BGR order instead of RGB

# a couple of utility functions for converting to and from Caffe's input image layout
def preprocess(net, img):
    try:
        return np.float32(np.rollaxis(img, 2)[::-1]) - net.transformer.mean['data']
    except ValueError:
        return np.float32(np.rollaxis(img, 1)[::-1]) - net.transformer.mean['data']

def deprocess(net, img):
    return np.dstack((img + net.transformer.mean['data'])[::-1])

# Producing dreams
def make_step(net, step_size=1.5, end='inception_4c/output', jitter=32, clip=True):
    '''Basic gradient ascent step.'''

    src = net.blobs['data'] # input image is stored in Net's 'data' blob
    dst = net.blobs[end]

    ox, oy = np.random.randint(-jitter, jitter+1, 2)
    src.data[0] = np.roll(np.roll(src.data[0], ox, -1), oy, -2) # apply jitter shift
            
    net.forward(end=end)
    dst.diff[:] = dst.data  # specify the optimization objective
    net.backward(start=end)
    g = src.diff[0]
    # apply normalized ascent step to the input image
    src.data[:] += step_size/np.abs(g).mean() * g

    src.data[0] = np.roll(np.roll(src.data[0], -ox, -1), -oy, -2) # unshift image
            
    if clip:
        bias = net.transformer.mean['data']
        src.data[:] = np.clip(src.data, -bias, 255-bias)

def deepdream(task_id, net, base_img, iter_n=10, octave_n=4, octave_scale=1.4, end='inception_4c/output', clip=True, **step_params):
    # set for celery task progress updates
    progress = 0
    # prepare base images for all octaves
    octaves = [preprocess(net, base_img)]
    for i in xrange(octave_n-1):
        octaves.append(nd.zoom(octaves[-1], (1, 1.0/octave_scale,1.0/octave_scale), order=1))
        progress = ((i+1.0)/(octave_n))*10+5
        current_task.update_state(task_id, 'PROGRESS', {'progress': progress})
    
    src = net.blobs['data']
    detail = np.zeros_like(octaves[-1]) # allocate image for network-produced details
    for octave, octave_base in enumerate(octaves[::-1]):
        h, w = octave_base.shape[-2:]
        if octave > 0:
            # upscale details from the previous octave
            h1, w1 = detail.shape[-2:]
            detail = nd.zoom(detail, (1, 1.0*h/h1,1.0*w/w1), order=1)

        src.reshape(1,3,h,w) # resize the network's input image size
        src.data[0] = octave_base+detail
        for i in xrange(iter_n):
            make_step(net, end=end, clip=clip, **step_params)
            progress = 15+85/(octave_n*iter_n-1.0)*(iter_n*octave+i)
            current_task.update_state(task_id, 'PROGRESS', {'progress': progress})

        # extract details produced on the current octave
        detail = src.data[0]-octave_base
    # returning the resulting image
    return deprocess(net, src.data[0])

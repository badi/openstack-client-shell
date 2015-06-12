from pxul.subprocess import run
from util import openstack_parse_show
from errors import TimeoutError
import operator
from functools import partial

import time

import logging
logger = logging.getLogger(__name__)


def image_show(identifier):
    cmd = ['glance', 'image-show', identifier]
    return run(cmd, capture='both')


def image_create(path, name,
                 public=True,
                 disk_format='qcow2',
                 container_format='bare'):
    """Create an image

    :param path: path to image on disk
    :param name: name of the image to create
    :param public: enable public access
    :param disk_format: the format of the image on disk
    :param container_format: format of image on glance
    :returns: identifier of the created image
    :rtype: str

    """
    logger.info('Creating image {name} from {path}'.format(**locals()))

    cmd = ['glance', 'image-create',
           '--is-public', str(public),
           '--disk-format', disk_format,
           '--container-format', container_format,
           '--name', name,
           '--file', path
           ]
    output = run(cmd, capture='both').out
    id = openstack_parse_show(output, 'id')
    logger.info('Created image {}'.format(id))
    return id


def wait_for_image_property(identifier, property, cmp_func,
                            wait=20,
                            maxtries=10):
    """Wait for an image to have a given property.
    Raises TimeoutError on failure.

    :param identifier: the image identifier
    :param property: the name of the property
    :param cmp_func: predicate function accepting current value of the property
    :param wait: time (in seconds) between polls
    :param maxtries: maximum number of attempts
    :returns: True
    """
    logger.info('Waiting for {identifier} to be {property} using {cmp_func}'
                .format(**locals()))

    for _ in xrange(maxtries):
        output = image_show(identifier)
        current = openstack_parse_show(output, 'status')
        if cmp_func(current):
            return True
        else:
            time.sleep(wait)

    msg = 'Timeout while waiting for image {identifier} {property} using {fn}'\
          .format(identifier=identifier, property=property, fn=cmp_func)
    logger.info(msg)
    raise TimeoutError(msg)


def image_download(identifier, path):
    """Download an openstack image to a file

    :param identifier: the identifier of the image
    :param path: path to download file
    """
    logger.info('Downloading {identifier} to {path}'.format(**locals()))

    active = partial(operator.eq, 'active')
    wait_for_image_property(identifier, 'state', active)

    cmd = ['glance', 'image-download',
           '--file', path,
           '--progress',
           identifier]
    run(cmd)


def image_delete(identifier):
    """Delete an image from glance

    :param identifier: identifier of the image
    """
    logger.info('Deleting image {}'.format(identifier))
    cmd = ['glance', 'image-delete', identifier]
    run(cmd)

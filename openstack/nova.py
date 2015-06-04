from util import shell
from util import openstack_parse_show
from errors import TimeoutError
from errors import ParseError

import uuid
import time
import socket
import logging
logger = logging.getLogger(__name__)


def wait_for_property(identifier, property, wait=10, maxtries=10):
    """Wait for a property to show up in a running instance.

    :param identifier: instance identifier
    :param property: property name
    :param wait: time (in seconds) between polls
    :param maxtries: number of attempts
    :returns: the property value
    :rtype: string
    """
    logger.info('Waiting for property {}'.format(property))

    for attempt in xrange(maxtries):
        output = show(identifier)
        try:
            value = openstack_parse_show(output, property)
        except ParseError:
            time.sleep(wait)
        else:
            return value

    raise TimeoutError('Waiting on {property} for instance {identifier}'
                       .format(property=property, identifier=identifier))


def wait_for_sshd(address, port=22, wait=10, maxtries=10):
    """Wait for sshd to start on the machine.

    Raises TimeoutError on failure.

    :param address: where sshd will be running
    :param port: port to connect to
    :param wait: time (in seconds) between polls
    :param maxtries: maximum number of attempts
    :returns: True if success
    """
    logger.info('Waiting for SSHD on {}'.format(address))

    s = socket.socket(socket.AF_INET)
    try:
        for attempt in xrange(maxtries):
            try:
                msg = '{attempt:>2} /{max:>3} Trying to connect to {address} on {port}'
                logger.debug(msg.format(attempt=attempt,
                                        max=maxtries,
                                        address=address, port=port))
                s.connect((address, port))
            except:
                logger.debug('Could not connect, sleeping for {wait}s'
                             .format(wait=wait))
                time.sleep(wait)
            else:
                return True
    finally:
        logger.debug('Closing socket to {}'.format(address))
        s.close()

    msg = 'Timeout while waiting for SSHD on {address}:{port}'\
          .format(address=address, port=port)
    logger.warning(msg)
    raise TimeoutError(msg)


def wait_for_machine(identifier, sshd=22, wait=10, maxtries=10):
    address = wait_for_property(identifier, 'int-net network',
                                wait=wait, maxtries=maxtries)
    wait_for_sshd(address, port=sshd, wait=wait, maxtries=maxtries)
    return address


def show(identifier):
    """Show the details of an instance

    :param identifier: the instance identifier
    :returns: the output of 'nova show'
    :rtype: string
    """
    cmd = ['nova', 'show', identifier]
    return shell(cmd)


def delete(identifier):
    logger.info('Deleting instance {}'.format(identifier))
    cmd = ['nova', 'delete', identifier]
    return shell(cmd)


def boot(image, name=None, keyname=None, flavor='m1.small'):
    logger.info('Booting {image} as {name} key {keyname} and flavor {flavor}'
                .format(**locals()))
    cmd = ['nova', 'boot',
           '--image', image,
           '--flavor', flavor
           ]\
        + (['--key-name', keyname] if keyname else [])\
        + [name or str(uuid.uuid4())]
    
    output = shell(cmd, capture=True)
    id = openstack_parse_show(output, 'id')
    return id


def image_show(identifier):
    """Show the details of an instance image.
    """
    cmd = ['nova', 'image-show', identifier]
    return shell(cmd, capture=True)


def image_create(identifier, name):
    """Create a snapshot of a running instance

    :param identifier: instance identifier
    :param name: name of the image to create
    :returns: the identifier of the image created
    :rtype: string
    """

    logger.info('Creating snapshot of {identifier} as {name}'
                .format(**locals()))

    cmd = ['nova', 'image-create', '--show', identifier, name]
    output = shell(cmd)
    uuid = openstack_parse_show(output, 'id')
    logger.info('Created snapshot {uuid}'.format(uuid=uuid))
    return uuid

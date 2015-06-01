from errors import ParseError

import subprocess
import pipes
import logging


def shell(cmd, capture=True):
    """Run a shell command

    :param cmd: the command to run as a list of arguments
    :param capture: capture the output
    """
    logger = logging.getLogger('shell')
    logger.debug('Got command', cmd)
    logger.debug('Executing', ' '.join(map(pipes.quote, cmd)))

    if capture:
        return subprocess.check_output(cmd)
    else:
        return subprocess.check_call(cmd)


def openstack_parse_show(output, property):
    """Parse the output of showing an openstack property to retreive an
    identifier's value.

    Raises ParseError on failure
    """
    def get_value(line, key, sep='|'):
        split = line.split(sep)

        if not len(split) == 4:
            return None

        key_found = split[1].strip()
        if key_found == key:
            return split[2].strip()

        else:
            return None

    if type(output) is str:
        output = output.split('\n')

    for line in output:
        val = get_value(line, property)
        if val:
            return val

    raise ParseError('Failed to parse {property} from:\n{output}'
                     .format(property=property, output=output))

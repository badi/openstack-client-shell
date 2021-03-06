from errors import ParseError

import logging
logger = logging.getLogger(__name__)


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
                     .format(property=property, output='\n'.join(output)))

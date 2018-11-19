from subprocess import check_call
import logging
from . import cache_dir


def acquire():
    """Use wget to download MIBs to cache.
    Wait 2 seconds between each MIB.
    """
    logging.info('Downloading MIBs to %s', cache_dir)
    command_components = [
        'wget',
        '--mirror',
        '--wait=2',
        '--directory-prefix=%s' % cache_dir,
        '--no-host-directories',
        '--cut-dirs=3',
        'ftp://ftp.cisco.com/pub/mibs/v2/'
    ]
    return_code = check_call(command_components)
    if return_code > 0:
        logging.info('Completed downloading MIBs.')
    else:
        logging.info('Download failed.')

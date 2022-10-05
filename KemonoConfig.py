from calendar import c
import os
import os.path
import argparse
import configparser


class KemonoConfig():

    # Defaul Values
    path = '.'
    handles = []
    name_mask = ''
    config_file = '.' + os.sep + 'kemono-config.cfg'

    log = False
    get_description = False
    confirm_download = False
    find_more_handles = False
    ignore_first_image = False

    image_max_size = -1
    video_max_size = -1
    number_of_posts = -1
    otherfile_max_size = -1

    titles_blacklist = []
    extensions_whitelist = []
    extensions_blacklist = []

    """
    >>> class A():
    ...     a = 12
    ...     b = 13
    ...     def __init__(self):
    ...             self.a = 0
    ...             self.b = 1
    ...     def printa(self):
    ...             for att, value in self.__dict__.items():
    ...                     print(att, '=', value)
    ...     def printb(self):
    ...             for att in A.__dict__.keys():
    ...                     if att[:2] != '__':
    ...                             value = getattr(A, att)
    ...                             if not callable(value):
    ...                                     print(att, '=', value)
    ...
    >>> a = A()
    >>> a.printa()
    a = 0
    b = 1
    >>> a.printb()
    a = 12
    b = 13
    """

    def __init__(self):

        arguments = self.get_arguments()

        for argument, value in arguments.items():
            setattr(self, argument, value)

        try:
            self.parse_configfile(override=arguments)
        except OSError:
            raise OSError

    def get_arguments(self):

        unit = 'KBYTES_SIZE'
        argparser = argparse.ArgumentParser()
        def positive_parser(str): return abs(int(str))

        argparser.add_argument('path',
                               help='local path to retrive stuff to')

        argparser.add_argument('handles', nargs='+',
                               help='string handles to search for the artist, like their Pixiv ID or name')

        argparser.add_argument('-C', '--config-file', metavar='FILE',
                               help='path to configuration file')

        argparser.add_argument('-f', '--find-more-handles', action='store_true',
                               help='best effort to find other handles based on the given ones')

        argparser.add_argument('-n', '--number-of-posts', nargs=1, type=positive_parser,
                               help='number of posts to look for stuff to download')

        argparser.add_argument('-c', '--confirm-download', action='store_true',
                               help='prompts user if they really want to download the amount of files found')

        argparser.add_argument('-i', '--ignore-first-image', action='store_true',
                               help='ignores the first image in a post')

        argparser.add_argument('--img-max-size', type=positive_parser, metavar=unit,
                               help='max size limit for images, in kilo bytes (default: any)')

        argparser.add_argument('--video-max-size', type=positive_parser, metavar=unit,
                               help='max size limit for videos, in kilo bytes (default: any)')

        argparser.add_argument('--other-file-max-size', type=positive_parser, metavar=unit,
                               help='max size limit for files that are not image nor video, in kilo bytes (default: any)')

        argparser.add_argument('-w', '--extensions-whitelist', nargs='+', metavar=('extension1', 'extension2'),
                               help='extensions whitelist: the script will only look for those')

        argparser.add_argument('-b', '--extensions-blacklist', nargs='+', metavar=('extension1', 'extension2'),
                               help='extensions blacklist')

        argparser.add_argument('-B', '--titles-blacklist', nargs='+', metavar=('word1', 'word2'),
                               help='posts with these words in their title will be skipped')

        argparser.add_argument('--name-mask',
                               help='string mask to name downloaded files')

        argparser.add_argument('-d', '--get-description', action='store_true',
                               help='also saves post\'s description in a text file with file\'s name')

        argparser.add_argument('-l', '--log', action='store_true',
                               help='enables log on console')

        return vars(argparser.parse_args())

    def get_default_values(self):

        default_values = {}
        for argument in KemonoConfig.__dict__.keys():
            if argument[:2] != '__' and argument not in ('path', 'handles', 'config_file'):
                value = getattr(KemonoConfig, argument)
                if not callable(value):
                    default_values.update({argument: value})

        return default_values

    def create_default_configfile(self):

        cparser = configparser.ConfigParser()
        default_values = self.get_default_values()
        with open(KemonoConfig.config_file, 'w') as cf:
            for argument, value in default_values.items():
                cparser.set('DEFAULT', argument, value)
            cparser.write(cf, space_around_delimiters=False)

    def parse_configfile(self, override=None):

        default_values = self.get_default_values()

        # Checks for provided config file.
        # Creates default config file if necessary
        if not os.path.exists(self.config_file):
            if self.config_file != KemonoConfig.config_file:
                raise OSError
            try:
                self.create_default_configfile()
            except OSError:
                raise OSError

        # Loads config file options into KemonoConfig instance
        cparser = configparser.ConfigParser()
        try:
            with open(self.config_file) as cf:
                content = cf.read()
                cparser.read_string(content)

                for option, value in default_values.items():
                    opt_type = type(value)
                    getoption = cparser.get

                    if opt_type == int:
                        getoption = cparser.getint
                    elif opt_type == bool:
                        getoption = cparser.getboolean

                    try:
                        value = getoption('DEFAULT', option)
                        if opt_type == list:
                            for string in value.split(','):

                        elif:

                    except configparser.NoOptionError:
                        continue

        except OSError:
            raise OSError

        # Overrides options with in-line arguments
        if override is not None:
            for argument, value in override.items():
                try:
                    self.__dict__[argument] = value
                except KeyError:
                    setattr(self, argument, value)

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

    def __init__(self):

        try:
            self.parse_configfile(override=self.get_arguments())
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

        argparser.add_argument('--image-max-size', type=positive_parser, metavar=unit,
                               help='max size limit for images, in kilo bytes (default: any)')

        argparser.add_argument('--video-max-size', type=positive_parser, metavar=unit,
                               help='max size limit for videos, in kilo bytes (default: any)')

        argparser.add_argument('--otherfile-max-size', type=positive_parser, metavar=unit,
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

    def check_configfile(self, cfile):

        # Checks for provided config file.
        # Creates default config file if necessary
        if not os.path.exists(cfile):
            if cfile != KemonoConfig.config_file:
                raise OSError

            cparser = configparser.ConfigParser()
            default_values = self.get_default_values()

            try:
                with open(KemonoConfig.config_file, 'w') as cf:
                    for argument, value in default_values.items():
                        cparser.set('DEFAULT', argument, str(value)
                                    if type(value) != list else '')
                    cparser.write(cf, space_around_delimiters=False)

            except OSError:
                raise OSError

    def parse_configfile(self, override=None):

        try:
            self.check_configfile(self.config_file)
        except OSError:
            raise OSError

        # Loads config file options into KemonoConfig instance
        cparser = configparser.ConfigParser()
        default_values = self.get_default_values()

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
                    except configparser.NoOptionError:
                        continue

                    setattr(self, option, value if opt_type != list else [
                            string for string in value.split(',') if string != ''])

        except OSError:
            raise OSError

        if override is None:
            return

        # Overrides options with in-line arguments
        for argument, value in override.items():
            if value != None and value != '':
                setattr(self, argument, value)

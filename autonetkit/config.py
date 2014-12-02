import ConfigParser
import os
import os.path

import pkg_resources
import validate
from autonetkit.exception import AutoNetkitException
from configobj import ConfigObj, flatten_errors

validator = validate.Validator()

# from http://stackoverflow.com/questions/4028904
ank_user_dir = os.path.join(os.path.expanduser("~"),  ".autonetkit")


class ConfigLoader(object):
    def __init__(self):
        self.load_pkg_cfg()

    def load_pkg_cfg(self):
        spec_file = pkg_resources.resource_filename('autonetkit',
                                                    '/config/configspec.cfg')
        self.config = ConfigObj(configspec=spec_file, encoding='UTF8')

    def load_configs(self):
        self.load_user_cfg()
        self.load_env_cfg()
        self.load_dir_cfg()

    def load_user_cfg(self):
        user_cfg_file = os.path.join(ank_user_dir, 'autonetkit.cfg')
        self.config.merge(ConfigObj(user_cfg_file))

    def load_env_cfg(self):
        self.config.merge(ConfigObj(os.environ.get('AUTONETKIT_CFG', '')))

    def load_dir_cfg(self):
        self.config.merge(ConfigObj('autonetkit.cfg'))

    @property
    def validator(self):
        return validator

    def validate(self):
        results = self.config.validate(self.validator)
        if results != True:
            for (section_list, key, _) in flatten_errors(self.config, results):
                if key is not None:
                    print "Error loading configuration file:"
                    print 'Invalid key "%s" in section "%s"' % \
                        (key, ', '.join(section_list))
                    raise AutoNetkitException
                else:
                    # ignore missing sections - use defaults
                    #print 'The following section was missing:%s ' % \
                    #    ', '.join(section_list)
                    pass


def load_config(config_loader_class=ConfigLoader):
    config_loader = config_loader_class()
    config_loader.load_configs()
    config_loader.validate()
    return config_loader.config

#NOTE: this only gets loaded once package-wide if imported as import autonetkit.config
settings = load_config()

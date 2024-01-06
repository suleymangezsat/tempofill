import configparser
import os


class ConfigReader:
    def __init__(self, config_file='config.ini'):
        self.config = configparser.ConfigParser()
        self.read_config(config_file)

    def read_config(self, config_file):
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"The configuration file {config_file} does not exist.")

        self.config.read(config_file)

    def get(self, section, option, fallback=None):
        try:
            return self.config.get(section, option)
        except (configparser.NoSectionError, configparser.NoOptionError):
            if fallback is not None:
                return fallback
            else:
                raise

    def get_secure(self, section, option, env_var):
        value = os.getenv(env_var)
        if value is not None:
            return value
        return self.get(section, option)
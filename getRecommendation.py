def getTravellingTime():
    pass

import configparser

config = configparser.ConfigParser()
config.read("./.properties")

for key in config['SECTION_HEADER']:
    print(key, config['SECTION_HEADER'][key])

api = config['SECTION_HEADER']['api']
print(api)
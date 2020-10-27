import os

secrets_dir = "/secrets"

for root, dirs, files in os.walk(secrets_dir):
    for file in files:
        try:
            with open(os.path.join(root, file), 'r') as secret_file:
                value = secret_file.read().strip()
                globals()[os.path.split(secret_file.name)[-1]] = value
        except IOError as e:
            raise IOError('Unable to read secrets from directory: \'/secrets\'')

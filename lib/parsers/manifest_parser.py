import yaml


def parse_manifest_file(content):
    data = yaml.safe_load(content)
    app = data.get('applications')
    result = {}
    if app and app[0].get('instances'):
        result = {'server_count': app[0]['instances']}
    return result


if __name__ == '__main__':
    filename = 'resources\\manifest.yml'
    with open(filename, 'r') as file:
        content = file.read()
    print(parse_manifest_file(content))

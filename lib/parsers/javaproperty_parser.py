def parse_java_property_file(content):
    keys = []
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('#') or not line:
            continue
        # Extract the key part (before the first '=')
        if 'AWS' in line.upper():
            key = line.split('=', 1)[0].strip()
            keys.append(key)
    return keys


if __name__ == '__main__':
    filename = 'resources\\pipeline.properties'
    with open(filename, 'r') as file:
        content = file.read()
    print(parse_java_property_file(content))
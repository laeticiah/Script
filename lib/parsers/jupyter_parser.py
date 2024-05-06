import nbformat
from nbconvert import PythonExporter
from nbconvert.preprocessors import Preprocessor

from boto3_parser import parse_boto3_file


class HandleMagicCommands(Preprocessor):
    def preprocess_cell(self, cell, resources, cell_index):
        if cell.cell_type == 'code':
            lines = cell.source.split('\n')
            processed_lines = []
            for line in lines:
                if line.startswith('%'):
                    processed_lines.append('# ' + line)
                else:
                    processed_lines.append(line)
            cell.source = '\n'.join(processed_lines)
        return cell, resources


def parse_notebook_file(notebook_content):
    nb = nbformat.reads(notebook_content, as_version=4)

    exporter = PythonExporter()
    exporter.register_preprocessor(HandleMagicCommands(), enabled=True)

    source, _ = exporter.from_notebook_node(nb)
    return parse_boto3_file(source)


if __name__ == '__main__':
    notebook_path = 'resources\\02.08-Sorting.ipynb'
    with open(notebook_path) as f:
        nb = f.read()
    print(parse_notebook_file(nb))

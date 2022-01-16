#!/bin/env python
"""Determines the minimum Python version that satisfies all installed dependencies.

https://github.com/pypa/pip/issues/5675
https://github.com/pypa/pip/issues/3121

https://github.com/di/pip-api
https://pypi.org/project/pip-shims/

$VIRTUAL_ENV/lib/python3.9/site-packages/

METADATA files:
https://packaging.python.org/en/latest/specifications/recording-installed-packages/
https://packaging.python.org/en/latest/specifications/core-metadata/
https://packaging.pypa.io/en/latest/specifiers.html
"""
from email.parser import Parser
from pathlib import Path
import sys

import packaging
from packaging.specifiers import SpecifierSet

PYTHON_VERSIONS = {
    '2.1',
    '2.2',
    '2.3',
    '2.4',
    '2.5',
    '2.6',
    '2.7',
    '3.0',
    '3.1',
    '3.2',
    '3.3',
    '3.4',
    '3.5',
    '3.6',
    '3.7',
    '3.8',
    '3.9',
    '3.10',
}
TROVE_PREFIX= 'Programming Language :: Python :: '


def main():
    if len(sys.argv) > 2:
        print('Usage: pymin.py [DIR]', file=sys.stderr)
    elif len(sys.argv) == 2:
        dir = Path(sys.argv[1])
    else:
        dir = Path(packaging.__file__).parent.parent

    # parse METADATA files
    meta = []
    for metadata_file in dir.glob('*/METADATA'):
        with open(metadata_file) as f:
            meta.append(Parser().parse(f, headersonly=True))

    # process py_requires
    spec = SpecifierSet()
    for pkg in meta:
        spec &= SpecifierSet(pkg.get('Requires-Python', ''))

    print('Requires-Python:', sorted(spec.filter(PYTHON_VERSIONS)))

    # process Trove classifiers
    versions = list(PYTHON_VERSIONS)
    for pkg in meta:
        troves = [ver.split(' :: ')[2]
                  for ver in pkg.get_all('Classifier', [])
                  if ver.startswith(TROVE_PREFIX)]
        troves = {ver for ver in troves if ver and ver[0].isdigit()}
        if not troves:
            continue

        # drop redundant major-only versions
        for ver in list(troves):
            if '.' in ver:
                troves.discard(ver.split('.')[0])

        versions = [v for v in versions if v in troves or v.split('.')[0] in troves]

    print('Classifiers:', sorted(versions))


if __name__ == '__main__':
    main()

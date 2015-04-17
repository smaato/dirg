from __future__ import print_function
import os

try:
    from setuptools import setup, find_packages, Command, convert_path
except ImportError:
    from distutils.core import setup, Command
    from distutils.util import convert_path


def _find_packages(where='.', exclude=()):
    """Return a list all Python packages found within directory 'where'

    'where' should be supplied as a "cross-platform" (i.e. URL-style) path; it
    will be converted to the appropriate local path syntax.  'exclude' is a
    sequence of package names to exclude; '*' can be used as a wildcard in the
    names, such that 'foo.*' will exclude all subpackages of 'foo' (but not
    'foo' itself).
    """
    out = []
    stack = [(convert_path(where), '')]
    while stack:
        where, prefix = stack.pop(0)
        for name in os.listdir(where):
            fn = os.path.join(where, name)
            if ('.' not in name and os.path.isdir(fn) and
                    os.path.isfile(os.path.join(fn, '__init__.py'))):
                out.append(prefix + name)
                stack.append((fn, prefix + name + '.'))
    for pat in list(exclude) + ['ez_setup', 'distribute_setup']:
        from fnmatch import fnmatchcase
        out = [item for item in out if not fnmatchcase(item, pat)]
    return out

find_packages = _find_packages

setup(
    name='dirg',
    version='1.0.0',
    packages=find_packages('.', exclude=('tests',)),
    description='A docker orchestration tool.',
    author='Stephan Brosinski',
    author_email='stephan.brosinski@smaato.com',
    url='https://github.com/smaato/dirg',
    download_url='https://github.com/smaato/dirg',
    license='MIT License',
    keywords=['docker', 'orchestration', 'docker-py'],
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
    ],
    package_data={'': ['LICENSE']},
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'dirg = dirg.dirg:main'
        ]
    },
    install_requires=['jinja2', 'docker-py>=1.1.0', 'pyyaml']
)

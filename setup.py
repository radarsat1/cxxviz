"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='srcml-to-mse',
    version='0.0.1',
    description='Tool to convert SrcML output from C++ analysis to MSE',
    long_description=long_description,
    url='https://github.com/radarsat1/cxxviz',

    # Author details
    author='Stephen Sinclair',
    author_email='stephen.sinclair@inria.cl',
    license='Apache2',
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Code Analysis',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: Apache2 License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],

    # What does your project relate to?
    keywords='analysis development visualisation',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),

    py_modules=['srcml-to-mse'],

    install_requires=['future'],

    extras_require={
        'dev': ['check-manifest'],
        'test': [],
    },

    package_data={
    },

    entry_points={
        'console_scripts': [
            #'srcml-to-mse=srcml_to_mse:main',
        ],
    },
)

# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

install_requires = ['numpy', 'sgp4']
version = "0.2.1"

setup(
    name='beyond',
    version=version,
    description="Flight Dynamic Library",
    platforms=["any"],
    keywords=['flight dynamic', 'satellite', 'space'],
    author='Jules David',
    author_email='jules@onada.fr',
    license='GPLv3',
    url="https://github.com/galactics/beyond",
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['beyond'],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Scientific/Engineering :: Astronomy",
        "Topic :: Scientific/Engineering :: Physics",
    ],
    install_requires=install_requires,
)

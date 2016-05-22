# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

install_requires = ['numpy']
version = "0.1"

setup(
    name='space-api',
    version=version,
    description="Flight Dynamic Library",
    platforms=["any"],
    keywords=['flight dynamic', 'satellite', 'space'],
    author='Jules David',
    author_email='jules@onada.fr',
    license='GPLv3',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['space'],
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
)

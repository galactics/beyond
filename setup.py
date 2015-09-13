# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

install_requires = []
version = "0.0.1"

setup(
    name='space',
    version=version,
    description="Flight Dynamic Library",
    platforms=["any"],
    keywords=['flight dynamic'],
    author='Jules David',
    author_email='jules@onada.fr',
    license='BSD',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['space'],
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
)

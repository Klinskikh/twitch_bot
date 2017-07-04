#!/usr/bin/env python

from setuptools import setup, find_packages

import bot

setup(
    name='twitch_bot',
    version=".".join(map(str, bot.__version__)),
    author='Klinskikh Anton',
    author_email='klinskih@gmail.com',
    url='https://github.com/Klinskikh/twitch_bot.git',
    install_requires=['livestreamer', 'requests'],
    description = 'A twitch viewer bot.',
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Operating System :: OS Independent",
        "Topic :: Software Development"
    ],
)
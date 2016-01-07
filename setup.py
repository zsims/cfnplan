from setuptools import setup
import os

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    long_description = readme.read()

from cfnplan import __version__

setup(
    name='cfnplan',
    version=__version__,
    author='Zachary Sims',
    author_email='zsims@users.noreply.github.com',
    packages=['cfnplan'],
    scripts=['scripts/cfnplan'],
    test_suite="tests",
    url='https://github.com/zsims/cfnplan',
    license='LICENSE.txt',
    description='Simple tool to help you plan for AWS CloudFormation stack updates',
    long_description=long_description,
    install_requires=[],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
    keywords='development aws cloudformation cloud',
    use_2to3=True
)


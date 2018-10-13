"""
Setup configuration
"""
from setuptools import setup


setup(
    name='pycalc',
    version='0.0.1',
    description='Pure-python command-line calculator.',
    url='https://github.com/melnik-ivan/pycalc.git',
    author='Ivan Melnik',
    author_email='ivan_melnik@epam.com',
    entry_points={
        'console_scripts': [
            'pycalc = pycalc.__main__:main'
        ]
    },
    license='MIT',
    packages=['pycalc'],
    zip_safe=False
)

from setuptools import setup
import os

os.mkdir('./bin')
os.rename('main.py', 'bin/pycalc')

setup(
    name='pycalc',
    version='0.0.1',
    description='Pure-python command-line calculator.',
    url='https://Ivan_Melnik@git.epam.com/Ivan_Melnik/pycalc.git/',
    author='Ivan Melnik',
    author_email='ivan_melnik@epam.com',
    scripts=['bin/pycalc'],
    license='MIT',
    packages=['pycalc'],
    zip_safe=False
)

os.rename('bin/pycalc', 'main.py')
os.rmdir('./bin')

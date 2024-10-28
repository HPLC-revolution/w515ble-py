# version 0.1.1, by Mark Tapsak, created 2024-08-28
# visit mtapsak@hotmail.com to purchase a pump converstion kit 

from setuptools import setup, find_packages

setup(
    name="w515ble-py",  
    version="0.1.0",   
    author="Mark Tapsak",
    author_email="mtapsak@hotmail.com",
    description="A Python package to control a Waters 515 HPLC pump fitted with a Virginia Analytical BlueTooth controller module",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/HPLC-revolution/w515ble-py",  
    packages=find_packages(),  
    install_requires=[
        "bleak>=0.13.0",  
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)

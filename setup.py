from setuptools import setup, find_packages

setup(
    name='pyhuelights',
    version='0.8.2',
    author='Srivatsan Iyer',
    author_email='supersaiyanmode.rox@gmail.com',
    packages=find_packages(),
    license='MIT',
    description='Library to remote control Philips Hue Lights',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    python_requires=">=3.10",
    install_requires=[
        "httpx",
        "zeroconf",
        "httpx-sse",
    ],
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)

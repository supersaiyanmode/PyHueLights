try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


setup(
    name='pyhuelights',
    version='0.8.0',
    author='Srivatsan Iyer',
    author_email='supersaiyanmode.rox@gmail.com',
    packages=[
        'pyhuelights',
    ],
    license='MIT',
    description='Library to remote control Philips Hue Lights',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    install_requires=[
        "requests[security]",
    ],
)

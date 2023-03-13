from setuptools import setup
from setuptools import find_packages

setup(
    name ='cbzPrintable' ,
    version='1.0.0',
    description='cbzPrintable',
    author='GrenManSK',
    install_requires=['argparse', 'glob2', 'numpy', 'PyPDF2', 'pillow'],
    packages=find_packages(exclude=('tests*', 'testing*')),
    entry_points={
        'console_scripts': [
            'cbzPrintable = cbzPrintable.cbzPrintable:main',
],
}
)

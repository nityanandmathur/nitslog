from setuptools import setup, find_packages

setup(
    name='nitslog',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'rich',
        'prompt_toolkit'
    ],
    entry_points={
        'console_scripts': [
            'nitslog=nitslog.logger:main',
        ],
    },
    author='Nityanand Mathur',
    author_email='nityanandmathur@gmail.com',
    description='A simple task logger application',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/tasklogger',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
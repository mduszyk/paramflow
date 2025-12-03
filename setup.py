from setuptools import setup, find_packages

setup(
    name='paramflow',
    version='0.5.5',
    description='A lightweight library for hyperparameter and configuration management', 
    packages=find_packages(),
    install_requires=[
        "pyyaml",
    ],
    extras_require={
        "dotenv": ["python-dotenv"],
    },
    entry_points={},
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/mduszyk/paramflow',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
)

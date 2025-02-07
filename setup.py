from setuptools import setup, find_packages

setup(
    name='paramflow',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        # any dependencies you want to include
    ],
    entry_points={
        'console_scripts': [
            'your-command=your_package.module:main_function',
        ],
    },
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/your-package',
    author='Your Name',
    author_email='youremail@example.com',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
)

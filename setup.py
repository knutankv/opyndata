import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="opyndata",
    version="1.0.0",
    author="",
    author_email="",
    description="OpyNDATA toolbox for import and postprocessing of measurement data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/knutankv/open-bridge-data",
    packages=setuptools.find_packages(),
    install_requires=['numpy', 'scipy', 'matplotlib', 'vispy'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6'
)
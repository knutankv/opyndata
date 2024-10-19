import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="opyndata",
    version="0.0.2",
    author="",
    author_email="",
    description="OpyNDATA toolbox for import and postprocessing of measurement data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/knutankv/opyndata",
    packages=setuptools.find_packages(),
    install_requires=['numpy', 'scipy', 'pandas', 'matplotlib', 'h5py', 'dash', 'plotly', 'datetime', 'flask'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6'
)

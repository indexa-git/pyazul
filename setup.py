import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

# Must update a few things in the setup
setuptools.setup(
    name="pyazul",
    version="0.2.0alpha",
    author="iterativo LLC",
    author_email="cristopher@iterativo.io",
    description="A library to make transaction using Azul webservices.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/iterativo-git/pyazul",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=['requests'],
    python_requires='>=3.6',
)

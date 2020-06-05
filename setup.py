import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

# Must update a few things in the setup
setuptools.setup(
    name="pyazul",
    version="0.4.1alpha",
    author="INDEXA Inc.",
    author_email="info@indexa.do",
    description="An Azul Webservices light wrapper for Python.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/indexa-git/pyazul/",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: OS Independent",
    ],
    install_requires=['requests'],
    python_requires='>=3.6',
)

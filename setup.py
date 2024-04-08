import setuptools

with open("README.md", "r", encoding = "utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name = "clap-detector",
    version = "2.0.4",
    author = "Tzur Soffer",
    author_email = "tzur.soffer@gmail.com",
    description = "A clap detector that can detect claps in patterns of single, double, etc.",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = "https://github.com/TzurSoffer/clapDetection",
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "numpy",
        "scipy",
        "pyaudio"
    ],
    package_dir = {"": "src"},
    packages = setuptools.find_packages(where="src")
)
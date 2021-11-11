from setuptools import setup, find_packages

# import os

setuptools.setup(
    name="BetaScope-DAQ",  # Replace with your own username
    version="0.1.0",
    author="UFSDLab",
    author_email="yuzhao@ucsc.edu",
    description="A small data acquisition tools for beta scope",
    long_description="A small data acquisition tools for beta scope",
    long_description_content_type="text/markdown",
    url="",
    package_dir={"": "src"},
    packages=find_packages(where="src", exclude=["tests"]),
    install_requires=[
        "pyvisa",
        "pyvisa-py",
        "pymodbus",
        "numpy",
        "coloredlogs",
        "configparser",
        "matplotlib",
        "plotext",
        "h5py",
        "tqdm",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Linux",
    ],
    python_requires=">=3.6",
    entry_points={"console_scripts": ["DAQ = DAQRunner:run_daq"]},
)

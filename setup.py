import setuptools


setuptools.setup(
    name="BetaDAQ",  # Replace with your own username
    version="0.1.0",
    author="UFSDLab",
    author_email="",
    description="A small data acquisition tools for beta scope",
    long_description="A small data acquisition tools for beta scope",
    long_description_content_type="text/markdown",
    url="",
    packages=setuptools.find_packages(
        "pyvisa, pyvisa-py, logging, coloredlogs, numpy, configparser",
    ),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Linux",
    ],
    python_requires=">=3.6",
    entry_points={"console_scripts": ["DAQ = DAQRunner:run_daq"]},
)

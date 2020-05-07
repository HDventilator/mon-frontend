import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="mon-frontend",
    version="0.0.1",
    author="HDventilator",
    author_email="noreply@github.com",
    description="Ventilator frontend",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/HDventilator/mon-fronten",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=["dash==1.12.0", "influxdb==5.3.0", "gunicorn==20.0.4",],
    include_package_data=True,
)

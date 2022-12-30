import setuptools

VERSION = "0.0.40"

PACKAGE_NAME = "module_qlr"
AUTHOR = "Valerio Luzzi"
EMAIL = "valerio.luzzi@gecosistema.com"
GITHUB = f"https://github.com/valluzzi/{PACKAGE_NAME}.git"
DESCRIPTION = "Create a qlr file definition"

setuptools.setup(
    name=PACKAGE_NAME,
    version=VERSION,
    author=AUTHOR,
    author_email=EMAIL,
    description=DESCRIPTION,
    long_description=DESCRIPTION,
    url=GITHUB,
    packages=setuptools.find_packages("src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_data={
        "": ["data/*.qlr"]
    },
    install_requires=[
        'numpy',
        'jenkspy',
        'matplotlib',
        'gdal',
        'gdal2numpy'
    ],

)

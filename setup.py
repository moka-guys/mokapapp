from setuptools import setup, find_packages

setup(
    name='mokapapp',
    version='1.0',
    description='Package to remove uploaded runfolders from \
        the Viapath Genome Informatics NGS workstation',
    url='https://github.com/NMNS93/wscleaner',
    author='Nana Mensah',
    author_email='gst-tr.MokaGuys@nhs.net',
    license='MIT',
    packages=find_packages(),
    zip_safe=False,
    python_requires='>=3.6.5',
    install_requires=['requests', 'pyodbc'],
    package_data={},
    entry_points={
        'console_scripts': [
            'mokapapp-query = mokapapp.query:main',
            'mokapapp-import = mokapapp.__main__:main'
        ]
    }
)

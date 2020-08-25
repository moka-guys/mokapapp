from setuptools import setup, find_packages

setup(
    name='mokapapp',
    version='1.0',
    description='Updates PanelApp panels in the Moka databse',
    url='https://github.com/moka-guys/mokapapp',
    author='Viapath Genome Informatics',
    author_email='gst-tr.MokaGuys@nhs.net',
    license='MIT',
    packages=find_packages(),
    zip_safe=False,
    python_requires='>=3.6.5',
    install_requires=['requests', 'pyodbc'],
    package_data={},
    entry_points={
        'console_scripts': [
            'mokapapp = mokapapp.app:main'
        ]
    }
)

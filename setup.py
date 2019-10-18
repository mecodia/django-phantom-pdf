import os
from setuptools import setup

README = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-phantom-pdf',
    version='0.4',
    packages=['phantom_pdf', 'phantom_pdf_bin'],
    package_data={'phantom_pdf_bin': ['*.js']},
    include_package_data=True,
    license='MIT License',
    description='A simple django app for creating pdf files.',
    long_description=README,
    url='https://github.com/mecoida/django-phantom-pdf',
    author='Juan Carizza, Tim Zenderman, Emiliano Dalla Verde Marcozzi, Tobias Birmilli, Tim Fischer',
    author_email='juan.carizza@gmail.com, tzenderman@gmail.com, edvm@fedoraproject.org, birmili@mecodia.de, fischer@mecodia.de',
    classifiers=[
            'Environment :: Web Environment',
            'Framework :: Django',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Topic :: Internet :: WWW/HTTP',
            "Topic :: Utilities",
        ],
)

from setuptools import setup, find_packages

description="""
Hstore module of django orm extensions package (collection of third party plugins build in one unified package).
"""

setup(
    name = "djorm-ext-hstore",
    version = '0.4.1',
    url = 'https://github.com/niwibe/djorm-ext-hstore',
    license = 'BSD',
    platforms = ['OS Independent'],
    description = description.strip(),
    author = 'Andrey Antukh',
    author_email = 'niwi@niwi.be',
    maintainer = 'Andrey Antukh',
    maintainer_email = 'niwi@niwi.be',
    packages = find_packages(),
    include_package_data = False,
    install_requires = [
        'djorm-ext-core >= 0.4.0',
        'djorm-ext-expressions >= 0.4.0',
    ],
    zip_safe = False,
    classifiers = [
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ]
)

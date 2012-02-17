from os.path import join, dirname
try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages
 
def get_requirements():
    reqsFile = open(join(dirname(__file__), 'requirements.txt'), 'r')
    reqs = [req.strip() for req in reqsFile if req.strip() != '']
    reqs.reverse() # we specify them in dependency resolution order in the file; we need to reverse that for install
    reqsFile.close()
    return reqs

def read(name, *args):
    try:
        with open(join(dirname(__file__), name)) as read_obj:
            return read_obj.read(*args)
    except Exception:
        return ''

extra_setup = {}

setup(
    name='powerglove-dns',
    version='1.0.0',
    author='Rob Dennis',
    author_email='rdennis+powerglove-dns@gmail.com',
    description="Reserves an appropriate ip in a PowerDNS installation for a given hostname, updating reverse/forward/text records as well",
    long_description=read('README.rst'),
    install_requires=get_requirements(),
    tests_require=['unittest2'],
    test_suite = 'unittest2.collector',
    entry_points="""
    [console_scripts]
    dns-assistant = dns_assistant:main
    """,
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Development Status :: 5 - Production/Stable',
    ],
    **extra_setup
)

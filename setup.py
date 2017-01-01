from distutils.core import setup

setup(
    name='RemoteBatch',
    version='0.0.1',
    packages=['boto', 'boto.s3', 'boto.ec2', 'boto.ec2.elb', 'boto.ec2.autoscale', 'boto.ec2.cloudwatch', 'boto.fps',
              'boto.rds', 'boto.sdb', 'boto.sdb.db', 'boto.sdb.db.manager', 'boto.sdb.persist', 'boto.sqs',
              'boto.sqs.20070501', 'boto.vpc', 'boto.mturk', 'boto.pyami', 'boto.pyami.installers',
              'boto.pyami.installers.ubuntu', 'boto.tests', 'boto.manage', 'boto.contrib', 'boto.mashups',
              'boto.services', 'boto.mapreduce', 'boto.cloudfront', 'view', 'model', 'pogoplug', 'controller'],
    url='https://channel3b.wordpress.com/RemoteBatch',
    license='Pending',
    author='Andy Fundinger',
    author_email='Andy@ciemaar.com',
    description='A simple attempt to delegate work from one machine to another, mostly Povray renders from a netbook to a desktop.'
)

#!/usr/bin/env python

"""Script to simplify file retrieval from S3.

Make sure your credentials are set up in ~/.boto as documented here:
http://boto.readthedocs.org/en/latest/boto_config_tut.html

"""

from __future__ import print_function

import argparse
import boto
import sys
import tarfile
import unittest

# Change this to whatever is convenient
DEFAULT_BUCKET_NAME = ''

def apply_filters(contents, filters):
    """Yield keys that pass all filters.

    contents: a list of S3 keys

    filters: a list of strings

    """
    for item in contents:
        yld = True
        for fil in filters:
            if fil not in item.name:
                yld = False
                break
        if yld:
            yield item


def format_bucket(bucket, contents):
    """Create a string containing bucket's name and number of keys."""
    return '[Bucket {}, {} items]'.format(bucket.name, len(contents))


def format_contents(contents):
    """Create a string listing of the bucket's contents."""
    result = []
    for item in contents:
        result.append('* {}'.format(item.name))
    return '\n'.join(result)


def bytes_to_mibibytes(num_bytes):
    """Convert bytes to mibibytes."""
    return num_bytes / 1024.0 / 1024.0


def format_bytes(num_bytes):
    return '{:.2f}MiB'.format(bytes_to_mibibytes(num_bytes))


def download_key(key):
    print('downloading {}...'.format(format_bytes(key.size)))
    def progress(cur, size):
        print('{}%...'.format(int(100 * float(cur) / float(size))))

    key.get_contents_to_filename(key.name, cb=progress)

    # nicholasbishop: I tried combining the download, decompress, and
    # untar steps but it did not go well. With a small buffer size it
    # downloaded very very slowly, and with a large buffer size it ate
    # up all my RAM and destroyed everything.
    with tarfile.open(key.name, 'r:bz2') as tar_file:
        tar_file.extractall()


def loop(bucket, filters):
    contents = list(apply_filters(bucket, filters))
    while True:
        print(format_bucket(bucket, contents))
        if len(contents) <= 9:
            print(format_contents(contents))

        if len(contents) == 1:
            download = raw_input('download and untar? [Y/n] ')
            if download.lower() == 'y' or download == '':
                download_key(contents[0])
            break
        else:
            fil = raw_input('filter: ')
            new_contents = list(apply_filters(contents, [fil]))
            if len(new_contents) == 0:
                print('no matches')
            else:
                contents = new_contents


def parse_args(argv):
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Utility for retrieving files from S3')
    bucket_help = 'S3 bucket name'
    if DEFAULT_BUCKET_NAME != '':
        bucket_help += ' (default={})'.format(DEFAULT_BUCKET_NAME)
    parser.add_argument('-b', '--bucket', default=DEFAULT_BUCKET_NAME,
                        metavar='bkt', help=bucket_help)
    parser.add_argument('filter', nargs='*',
                        help='only search keys containing these terms')
    args = parser.parse_args(argv)
    if args.bucket == '':
        parser.error('invalid bucket name')
    return args


def main(argv):
    args = parse_args(argv)
    bucket_name = args.bucket
    filters = args.filter

    print('Connecting...')

    conn = boto.connect_s3()

    bucket = conn.get_bucket(bucket_name)
    loop(bucket, filters)


if __name__ == '__main__':
    main(sys.argv[1:])


class Tests(unittest.TestCase):
    """Unit tests."""

    class MockKey(object):
        """Mock boto S3 key."""
        # pylint: disable=too-few-public-methods
        def __init__(self, name):
            self.name = name

    def test_bytes_to_mibibytes(self):
        """Test bytes_to_mibibytes."""
        self.assertEqual(bytes_to_mibibytes(1048576), 1)
        self.assertEqual(bytes_to_mibibytes(1048576 / 2), 0.5)

    def test_apply_filters(self):
        """Test apply_filters."""
        inp = [Tests.MockKey('foo bar')]
        self.assertEqual(list(apply_filters(inp, ['foo'])), inp)
        self.assertEqual(list(apply_filters(inp, ['zoo'])), [])

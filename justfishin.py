#!/usr/bin/env python

# Copyright 2015 Neverware
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Script to simplify file retrieval from S3.

Make sure your credentials are set up in ~/.boto as documented here:
http://boto.readthedocs.org/en/latest/boto_config_tut.html

"""

from __future__ import print_function

import argparse
import boto
import os
import sys
import tarfile
import unittest

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

#TODO: consider renaming to clarify that this method also extracts
def download_key(key):
    print('downloading {}...'.format(format_bytes(key.size)))
    def progress(cur, size):
        print('{}%...'.format(int(100 * float(cur) / float(size))))

    key.get_contents_to_filename(key.name, cb=progress)

    # nicholasbishop: I tried combining the download, decompress, and
    # untar steps but it did not go well. With a small buffer size it
    # downloaded very very slowly, and with a large buffer size it ate
    # up all my RAM and destroyed everything.
    print('extracting...')
    with tarfile.open(key.name, 'r:*') as tar_file:
        def is_within_directory(directory, target):
            
            abs_directory = os.path.abspath(directory)
            abs_target = os.path.abspath(target)
        
            prefix = os.path.commonprefix([abs_directory, abs_target])
            
            return prefix == abs_directory
        
        def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
        
            for member in tar.getmembers():
                member_path = os.path.join(path, member.name)
                if not is_within_directory(path, member_path):
                    raise Exception("Attempted Path Traversal in Tar File")
        
            tar.extractall(path, members, numeric_owner=numeric_owner) 
            
        
        safe_extract(tar_file)


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


def get_default_bucket_name():
    """Return stripped contents of cwd/default_bucket"""
    file_name = 'default_bucket'
    if os.path.exists(file_name):
        with open(file_name, 'r') as bucket_file:
            return bucket_file.read().strip()


def parse_args(argv):
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Utility for retrieving files from S3')
    bucket_help = 'S3 bucket name'
    default_bucket_name = get_default_bucket_name()
    if default_bucket_name is not None:
        bucket_help += ' (default={})'.format(default_bucket_name)
    parser.add_argument('-b', '--bucket', default=default_bucket_name,
                        metavar='bkt', help=bucket_help)
    parser.add_argument('filter', nargs='*',
                        help='only search keys containing these terms')
    args = parser.parse_args(argv)
    if args.bucket is None:
        parser.error('invalid bucket name; create "default_bucket" file or pass "-b"')
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

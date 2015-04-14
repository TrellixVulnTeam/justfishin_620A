# justfishin

Simple tool for file retrieval from S3

Make sure your credentials are set up in ~/.boto as documented here:
http://boto.readthedocs.org/en/latest/boto_config_tut.html

For convenience, the script looks for a file in the current working
directory called "default_bucket". If found, the first line of the
file will be used as the default bucket name. Otherwise `--bucket` is
required.


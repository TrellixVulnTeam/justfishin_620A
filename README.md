# justfishin

Simple tool for file retrieval from S3. If you want to retrieve one
file from a bucket with lots of similar names, this tool can help.

# Getting started

Make sure your credentials are set up in ~/.boto as documented here:
http://boto.readthedocs.org/en/latest/boto_config_tut.html

Run the script like this: `./justfishin.py --bucket my-bucket foo bar`

This will get the full list of files in `my-bucket` and filter the
list down to just the names that include all search terms. Example
names that would match in this case: `foo-bar-1`, `bar-foo-2`. Names
that would not match: `just-foo-1`, `just-bar-2`. You can specify any
number of terms, including zero.

If there are multiple matches, the script will enter an interactive
filter mode where you can filter down the list further.

Once there is only one match, it will offer to download and untar the
file. Currently it only handles bzip'd tar files (patches welcome to
extend it for other uses.)

# Default bucket

For convenience, the script looks for a file in the current working
directory called "default_bucket". If found, the first line of the
file will be used as the default bucket name. Otherwise `--bucket` is
required.

# -*- coding: utf-8 -*-

"""
This module provides utility functions that are used within the script.
"""

import errno
import os
import random
import re
import string
import sys

import six
from bs4 import BeautifulSoup as BeautifulSoup_

# Force us of bs4 with html5lib
BeautifulSoup = lambda page: BeautifulSoup_(page, 'html5lib')

from .define import COURSERA_URL

from six.moves import html_parser

#  six.moves doesn’t support urlparse
if six.PY3:  # pragma: no cover
    from urllib.parse import urlparse, urljoin
else:
    from urlparse import urlparse, urljoin

# Python3 (and six) don't provide string
if six.PY3:
    from string import ascii_letters as string_ascii_letters
    from string import digits as string_digits
else:
    from string import letters as string_ascii_letters
    from string import digits as string_digits


if six.PY2:
    def decode_input(x):
        stdin_encoding = sys.stdin.encoding
        if stdin_encoding is None:
            stdin_encoding = "UTF-8"
        return x.decode(stdin_encoding)
else:
    def decode_input(x):
        return x


def random_string(length):
    """
    Return a pseudo-random string of specified length.
    """
    valid_chars = string_ascii_letters + string_digits

    return ''.join(random.choice(valid_chars) for i in range(length))


def clean_filename(s, minimal_change=False):
    """
    Sanitize a string to be used as a filename.

    If minimal_change is set to true, then we only strip the bare minimum of
    characters that are problematic for filesystems (namely, ':', '/' and
    '\x00', '\n').
    """

    # First, deal with URL encoded strings
    h = html_parser.HTMLParser()
    s = h.unescape(s)

    # Strip forbidden characters
    s = (
        s.replace(':', '-')
        .replace('/', '-')
        .replace('\x00', '-')
        .replace('\n', '')
    )

    if minimal_change:
        return s

    s = s.replace('(', '').replace(')', '')
    s = s.rstrip('.')  # Remove excess of trailing dots

    s = s.strip().replace(' ', '_')
    valid_chars = '-_.()%s%s' % (string.ascii_letters, string.digits)
    return ''.join(c for c in s if c in valid_chars)


def get_anchor_format(a):
    """
    Extract the resource file-type format from the anchor.
    """

    # (. or format=) then (file_extension) then (? or $)
    # e.g. "...format=txt" or "...download.mp4?..."
    fmt = re.search(r"(?:\.|format=)(\w+)(?:\?.*)?$", a)
    return fmt.group(1) if fmt else None


def mkdir_p(path, mode=0o777):
    """
    Create subdirectory hierarchy given in the paths argument.
    """

    try:
        os.makedirs(path, mode)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def fix_url(url):
    """
    Strip whitespace characters from the beginning and the end of the url
    and add a default scheme.
    """
    if url is None:
        return None

    url = url.strip()

    if url and not urlparse(url).scheme:
        url = "http://" + url

    return url


def make_coursera_absolute_url(url):
    """
    If given url is relative adds coursera netloc,
    otherwise returns it without any changes.
    """

    if not bool(urlparse(url).netloc):
        return urljoin(COURSERA_URL, url)

    return url


def extract_supplement_links(page):
    """
    Extract supplement links from the html page that contains <a> tags
    with href attribute.

    @param page: HTML page.
    @type page: str

    @return: Dictionary with supplement links grouped by extension.
    @rtype: {
        '<extension1>': [
            ('<link1>', ''),
            ('<link2>', '')
        ],
        'extension2': [
            ('<link3>', ''),
            ('<link4>', '')
        ]
    }
    """
    soup = BeautifulSoup(page)
    links = [item['href']
             for item in soup.find_all('a') if 'href' in item.attrs]
    links = sorted(list(set(links)))
    supplement_links = {}

    for link in links:
        filename, extension = os.path.splitext(link)
        # Some courses put links to sites in supplement section, e.g.:
        # http://pandas.pydata.org/
        if extension is '':
            continue

        # Make lowercase and cut the leading/trailing dot
        extension = extension.lower().strip('.')
        basename = os.path.basename(filename)
        if extension not in supplement_links:
            supplement_links[extension] = []
        # Putting basename into the second slot of the tuple is important
        # because that will allow to download many supplements within a
        # single lecture, e.g.:
        # 01_slides-presented-in-this-module.pdf
        # 01_slides-presented-in-this-module_Dalal-cvpr05.pdf
        # 01_slides-presented-in-this-module_LM-3dtexton.pdf
        supplement_links[extension].append((link, basename))

    return supplement_links

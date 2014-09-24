from __future__ import absolute_import, division, print_function

import codecs
import logging
import os

import six

from bs4 import BeautifulSoup
from characteristic import Attribute, attributes
from zope.interface import implementer

from . import types
from .utils import APPLE_REF_TEMPLATE, ParserEntry, has_file_with, IParser


log = logging.getLogger(__name__)


PYDOCTOR_HEADER = b'''\
      This documentation was automatically generated by
      <a href="https://launchpad.net/pydoctor/">pydoctor</a>'''

PYDOCTOR_HEADER_OLD = b'''\
      This documentation was automatically generated by
      <a href="http://codespeak.net/~mwh/pydoctor/">pydoctor</a>'''


@implementer(IParser)
@attributes([Attribute("doc_path", instance_of=six.text_type)])
class PyDoctorParser(object):
    """
    Parser for pydoctor-based documentation: mainly Twisted.
    """
    name = 'pydoctor'

    @classmethod
    def detect(self, path):
        return has_file_with(
            path, "index.html", PYDOCTOR_HEADER
        ) or has_file_with(
            path, "index.html", PYDOCTOR_HEADER_OLD
        )

    def parse(self):
        """
        Parse pydoctor docs at *doc_path*.

        yield `ParserEntry`s
        """
        soup = BeautifulSoup(
            codecs.open(
                os.path.join(self.doc_path, 'nameIndex.html'),
                mode="r", encoding="utf-8",
            ),
            'lxml'
        )
        for tag in soup.body.find_all(u'a'):
            path = tag.get(u'href')
            if path and not path.startswith(u'#'):
                name = tag.string
                yield ParserEntry(
                    name=name,
                    type=_guess_type(name, path),
                    path=six.text_type(path)
                )

    def find_and_patch_entry(self, soup, entry):
        link = soup.find(u'a', attrs={'name': entry.anchor})
        if link:
            tag = soup.new_tag(u'a')
            tag['name'] = APPLE_REF_TEMPLATE.format(entry.type, entry.name)
            link.insert_before(tag)
            return True
        else:
            return False


def _guess_type(name, path):
    """
    Employ voodoo magic to guess the type of *name* in *path*.
    """
    if name.rsplit(u'.', 1)[-1][0].isupper() and u'#' not in path:
        return types.CLASS
    elif name.islower() and u'#' not in path:
        return types.PACKAGE
    else:
        return types.METHOD

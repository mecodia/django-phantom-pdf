# -*- coding: utf-8 -*-
import json
import logging
from subprocess import Popen, STDOUT, PIPE
import os
import phantom_pdf_bin
import uuid

try:
    # python 2.7
    from urllib import urlencode
    from urlparse import urlsplit
except ImportError:
    # python 3+
    from urllib.parse import urlencode, urlsplit

from django.conf import settings
from django.http import HttpResponse


logger = logging.getLogger(__name__)


# Path to generate_pdf.js file. Its distributed with this django app.
GENERATE_PDF_JS = os.path.join(os.path.dirname(phantom_pdf_bin.__file__),
                               'generate_pdf.js')
PHANTOM_ROOT_DIR = '/tmp/phantom_pdf'
DEFAULT_SETTINGS = dict(
    PHANTOMJS_COOKIE_DIR=os.path.join(PHANTOM_ROOT_DIR, 'cookies'),
    PHANTOMJS_GENERATE_PDF=GENERATE_PDF_JS,
    PHANTOMJS_PDF_DIR=os.path.join(PHANTOM_ROOT_DIR, 'pdfs'),
    PHANTOMJS_BIN='phantomjs',
    PHANTOMJS_FORMAT='A4',
    PHANTOMJS_ORIENTATION='landscape',
    PHANTOMJS_MARGIN=0,
    KEEP_PDF_FILES=False,
)


class RequestToPDF(object):
    """Class for rendering a requested page to a PDF."""

    def __init__(self, **kwargs):
        """Arguments:
            PHANTOMJS_COOKIE_DIR = Directory where the temp cookies will be saved.
            PHANTOMJS_PDF_DIR = Directory where you want to the PDF to be saved temporarily.
            PHANTOMJS_BIN = Path to PhantomsJS binary.
            PHANTOMJS_GENERATE_PDF = Path to generate_pdf.js file.
            KEEP_PDF_FILES = Option to not delete the PDF file after rendering it.
            PHANTOMJS_FORMAT = Page size to use.
            PHANTOMJS_ORIENTATION = How the page will be positioned when printing.
            PHANTOMJS_MARGIN = The margins of the PDF.
        """
        for attr, default_value in DEFAULT_SETTINGS.items():
            value = kwargs.get(attr) or getattr(settings, attr, default_value)
            setattr(self, attr, value)

        if not os.path.isfile(self.PHANTOMJS_BIN):
            raise RuntimeError("{} doesn't exist, read the docs for more info.".format(self.PHANTOMJS_BIN))

        for directory in (self.PHANTOMJS_COOKIE_DIR, self.PHANTOMJS_PDF_DIR):
            if not os.path.isdir(directory):
                os.makedirs(directory)

    def _build_url(self, request, get_data):
        """Build the url for the request."""
        protocol, domain, path, query, fragment = urlsplit(request.build_absolute_uri())
        if get_data:
            custom_query = urlencode(get_data)
        else:
            custom_query = ''
        return '{protocol}://{domain}{path}?{query}'.format(
            protocol=protocol,
            domain=domain,
            path=path,
            query=custom_query
        )

    def _save_cookie_data(self, request):
        """Save csrftoken and sessionid in a cookie file for authentication."""
        cookie_file = os.path.join(self.PHANTOMJS_COOKIE_DIR, str(uuid.uuid1())) + '.cookie.txt'
        cookie = '{cookie} {session}'.format(
            cookie=request.COOKIES.get(settings.CSRF_COOKIE_NAME, 'nocsrftoken'),
            session=request.COOKIES.get(settings.SESSION_COOKIE_NAME, 'nosessionid')
        )
        with open(cookie_file, 'w+') as fh:
            fh.write(cookie)
        return cookie_file

    def _set_source_file_name(self, basename=str(uuid.uuid1())):
        """Return the original source filename of the pdf."""
        return os.path.join(self.PHANTOMJS_PDF_DIR, basename) + '.pdf'

    def _return_response(self, file_src, basename):
        """Read the generated pdf and return it in a django HttpResponse."""
        # Open the file created by PhantomJS
        with open(file_src, 'rb') as f:
            return_file = f.readlines()

        response = HttpResponse(return_file, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename={filename}.pdf'.format(filename=basename)

        if not self.KEEP_PDF_FILES:  # remove generated pdf files
            os.remove(file_src)

        return response

    def request_to_pdf(self, request, basename,
                       format=None,
                       orientation=None,
                       margin=None,
                       make_response=True,
                       get_data=None):
        """Receive request, basename and return a PDF in an HttpResponse.
            If `make_response` is True return an HttpResponse otherwise file_src. """

        format = format or self.PHANTOMJS_FORMAT
        orientation = orientation or self.PHANTOMJS_ORIENTATION
        margin = margin or self.PHANTOMJS_MARGIN

        file_src = self._set_source_file_name(basename=basename)
        try:
            os.remove(file_src)
            logger.info("Removed already existing file: %s", file_src)
        except OSError:
            pass

        cookie_file = self._save_cookie_data(request)
        url = self._build_url(request, get_data)

        domain = urlsplit(
            request.build_absolute_uri()
        ).netloc.split(':')[0]

        # Some servers have SSLv3 disabled, leave
        # phantomjs connect with others than SSLv3
        ssl_protocol = "--ssl-protocol=ANY"
        try:
            phandle = Popen([
                self.PHANTOMJS_BIN,
                ssl_protocol,
                self.PHANTOMJS_GENERATE_PDF,
                url,
                file_src,
                cookie_file,
                domain,
                format,
                orientation,
                json.dumps(margin),
            ], close_fds=True, stdout=PIPE, stderr=STDOUT)
            phandle.communicate()

        finally:
            # Make sure we remove the cookie file.
            os.remove(cookie_file)

        return self._return_response(file_src, basename) if make_response else file_src


def render_to_pdf(request, basename,
                  format=None,
                  orientation=None,
                  margin=None,
                  make_response=True,
                  get_data=None):
    """Helper function for rendering a request to pdf.
    Arguments:
        request = django request.
        basename = string to use for your pdf's filename.
        format = the page size to be applied; default if not given.
        orientation = the page orientation to use; default if not given.
        make_response = create or not an HttpResponse
    """
    request2pdf = RequestToPDF()
    response = request2pdf.request_to_pdf(request, basename, format=format,
                                          orientation=orientation, margin=margin, make_response=make_response, get_data=get_data)
    return response

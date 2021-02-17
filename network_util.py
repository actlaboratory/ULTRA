from contextlib import contextmanager
import pypac, os

@contextmanager
def pac_context_for_url(url="https://www.actlab.org/", proxy_auth=None):
    """
    This context manager provides a simple way to add rudimentary PAC functionality
    to code that cannot be modified to use :class:`PACSession`,
    but obeys the ``HTTP_PROXY`` and ``HTTPS_PROXY`` environment variables.

    Upon entering this context, PAC discovery occurs with default parameters.
    If a PAC is found, then it's asked for the proxy to use for the given URL.
    The proxy environment variables are then set accordingly.

    Note that this provides a very simplified PAC experience that's insufficient for some scenarios.

    :param url: Consult the PAC for the proxy to use for this URL. Default is "https://www.actlab.org/"
    :param requests.auth.HTTPProxyAuth proxy_auth: Username and password proxy authentication.
    """
    prev_http_proxy, prev_https_proxy = os.environ.get('HTTP_PROXY'), os.environ.get('HTTPS_PROXY')
    pac = pypac.get_pac()
    if pac:
        resolver = pypac.ProxyResolver(pac, proxy_auth=proxy_auth)
        proxies = resolver.get_proxy_for_requests(url)
        # Cannot set None for environ. (#27)
        os.environ['HTTP_PROXY'] = proxies.get('http') or ''
        os.environ['HTTPS_PROXY'] = proxies.get('https') or ''
    yield
    if prev_http_proxy:
        os.environ['HTTP_PROXY'] = prev_http_proxy
    elif 'HTTP_PROXY' in os.environ:
        del os.environ['HTTP_PROXY']
    if prev_https_proxy:
        os.environ['HTTPS_PROXY'] = prev_https_proxy
    elif 'HTTPS_PROXY' in os.environ:
        del os.environ['HTTPS_PROXY']


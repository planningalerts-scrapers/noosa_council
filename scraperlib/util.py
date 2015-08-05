import re
import requests
from urlparse import urljoin


class AspJsLink(object):
    """ Wraps a given asp.net doPostBack href, and attempts
        to make something "clickable" out of it.

        eg. Given something like this:

            <a href="javascript:__doPostBack('ctl00$Content$cusResultsGrid$repWebGrid$ctl00$grdWebGridTabularView','Page$1')">1</a>

        This class extracts the target, the argument, and
        enough of the current page state to carry out the same
        request that this javascript call would have executed.

        ** Parameters **

        :param base_url: The url of the current page, so if the form action is
                         a relative link, we can build a fully qualified target.
        :param page_tree: lxml element tree of the page contents. Or anything similar
                          that provides the same xpath() query ability.
        :param js_href: The javascript href to be parsed.
        :param form_id: The id of the asp page form being submitted.
                        For "master" pages, this defaults to `aspnetForm`.
    """
    def __init__(self, base_url, page_tree, js_href, form_id="aspnetForm"):
        self.page = page_tree
        self.form_id = form_id
        self.form_action = self.page.xpath("//form[@id='{0}']/@action".format(form_id))[0]
        self.event_target, self.event_argument = self.parse_js_href(js_href)
        self.action_url = urljoin(base_url, self.form_action)

        self.load_state()

    def parse_js_href(self, js_href):
        params = re.match("javascript:__doPostBack\('(.*)'\s*,\s*'(.*)'\)", js_href)
        if params:
            return params.groups()
        raise ValueError("Invalid javascript doPostBack: {}".format(js_href))

    def get_page_var(self, var_id, attrib='value'):
        try:
            var = self.page.xpath("//form[@id='{}']//input[@id='{}']".format(
                self.form_id, var_id
            ))
        except Exception, err:
            print("Failed to find {} in page [{}]".format(var_id, err))
        else:
            if var:
                return getattr(var[0], attrib)

    def load_state(self):
        """ Hunt down all the asp.net page state values
            needed for our link click.
        """
        self.form_data = {
            '__EVENTTARGET': self.event_target,
            '__EVENTARGUMENT': self.event_argument,
        }

        page_vars = [
            '__VIEWSTATE', '__EVENTVALIDATION'
        ]
        for var_id in page_vars:
            self.form_data[var_id] = self.get_page_var(var_id)

    def click(self):
        """ Submits form post request, returns response content. """

        response = requests.post(
            self.action_url,
            data=self.form_data,
        )
        # Explode on errors. No-op if all ok.
        response.raise_for_status()
        return response.text

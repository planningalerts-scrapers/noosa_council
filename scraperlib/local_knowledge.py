
def get_application_links(browser, page_url):
    """ This routine hunts down all the development application links,
        within the given page.

        Each of these links should be yielded back to the caller, or
        all returned at once in an iterable result (eg. list).
    """
    browser.visit(page_url)
    pages = get_pagination_links(browser)
    finished = False

    while not finished:
        link_table_id = "ctl00_Content_cusResultsGrid_repWebGrid_ctl00_grdWebGridTabularView"
        links = browser.find_by_xpath(
            "id('{}')//tr[@class!='headerRow' and @class!='pagerRow']/td[1]/a".format(
                link_table_id
            )
        )

        for link in links:
            yield link['href']

        if pages:
            next_page = pages.pop(0)
            page_link = browser.find_link_by_href(next_page)
            page_link.click()
        else:
            finished = True


def extract_application_details(browser, application_url):
    """ Find all relevant development application information,
        from the details url we're given.

        The result should be one dictionary having the fields
        expected by a morph_planningalerts.DevelopmentApplication record.
    """
    raise NotImplementedError()


def get_pagination_links(browser):
    page_links = browser.find_by_xpath(".//tr[@class='pagerRow']//a")
    return [link["href"] for link in page_links]

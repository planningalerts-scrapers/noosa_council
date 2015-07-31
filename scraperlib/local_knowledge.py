
def get_application_links(browser, page_url):
    """ This routine hunts down all the development application links,
        within the given page.

        Each of these links should be yielded back to the caller, or
        all returned at once in an iterable result (eg. list).
    """
    raise NotImplementedError()


def extract_application_details(browser, application_url):
    """ Find all relevant development application information,
        from the details url we're given.

        The result should be one dictionary having the fields
        expected by a morph_planningalerts.DevelopmentApplication record.
    """
    raise NotImplementedError()

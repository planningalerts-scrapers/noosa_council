from collections import OrderedDict
from datetime import datetime
from morph_planningalerts import DevelopmentApplication

# NOTE: There doesn't seem to be a direct email address for application enquiries.
#   Closest thing they have is this form, which will unfortunately need the user
#   to hunt for the property they want to comment on... :(
ENQUIRY_URL = "https://noosa-eproperty.t1cloud.com/NOOEPRPROD/P1/eRequest/SubmitRequest.aspx?r=P1.WEBGUEST&f=%24P1.ECR.SUBMIT.MNT&Group=DevelopReq&GroupCategory=RMDevEnqui"


def get_application_links(browser, page_url):
    """ This routine hunts down all the development application links,
        within the given page.

        Each of these links should be yielded back to the caller, or
        all returned at once in an iterable result (eg. list).
    """
    browser.visit(page_url)
    pages = get_pagination_links(browser)
    finished = False

    applications = OrderedDict()

    # NOTE: We walk all the listed pages for links now,
    #   since we don't get to backtrack to a specific pagenation
    #   once we visit the detail page. The lists all share the same
    #   url, with page selection controlled by javascript form submits. :P
    while not finished:
        link_table_id = "ctl00_Content_cusResultsGrid_repWebGrid_ctl00_grdWebGridTabularView"
        links = browser.find_by_xpath(
            "id('{}')//tr[@class!='headerRow' and @class!='pagerRow']/td[1]/a".format(
                link_table_id
            )
        )

        for link in links:
            # Screw the href we're given here. It's a javascript
            # postback. Instead, we'll use the target url that the
            # normal form submit + redirect would send us to.
            target_url = "https://noosa-eproperty.t1cloud.com/NOOEPRPROD/P1/eTrack/eTrackApplicationDetails.aspx?r=P1.WEBGUEST&f=$P1.ETR.APPDET.VIW&ApplicationId={}".format(
                link.text
            )
            applications[link.text] = target_url

        if pages:
            next_page = pages.pop(0)
            page_link = browser.find_link_by_href(next_page)
            page_link.click()
        else:
            finished = True

    # Council ref is the link text. If we can skip now,
    # No need to fetch the detail page later.
    council_refs = applications.keys()

    # Fetch the already-seen list from our database...
    known_applications = DevelopmentApplication.select().where(
        DevelopmentApplication.council_reference.in_(council_refs)
    )

    for known in known_applications:
        applications[known.council_reference] = None
    return applications.values()


def extract_application_details(browser, application_url):
    """ Find all relevant development application information,
        from the details url we're given.

        The result should be one dictionary having the fields
        expected by a morph_planningalerts.DevelopmentApplication record.
    """
    browser.visit(application_url)

    display_map = {
        u'Application Number': 'council_reference',
        u'Address': 'address',
        u'Description': 'description',
        u'Submitted Date': ('date_received', lambda d: datetime.strptime(d, '%d/%m/%Y').date()),
    }

    try:
        display_names = [
            element.text
            for element in browser.find_by_xpath(
                ".//tr[@class='normalRow' or @class='alternateRow']/td[1]"
            )
        ]
        field_values = [
            element.text
            for element in browser.find_by_xpath(
                ".//tr[@class='normalRow' or @class='alternateRow']/td[2]"
            )
        ]

        fields = dict(zip(display_names, field_values))

        result = {}
        for display_name, value in fields.items():
            display_name = display_name.strip()
            value = value.strip()

            field_name = display_map.get(display_name)
            if field_name:
                if isinstance(field_name, tuple):
                    field_name, modifier = field_name
                    value = modifier(value)
                if field_name == 'address' and 'address' in result:
                    # Some of these applications have multiple
                    # properties attached to the one application. o_O
                    # Unsure how to handle, so just concatenating the
                    # addresses for now, and hoping google's geolocate
                    # sorts it out.
                    result[field_name] += ", " + value
                else:
                    result[field_name] = value

        # Sometimes there is no description...
        # At least this way, there'll be something kind of
        # describy.
        if 'Application Type' in fields:
            result['description'] = " - ".join([
                part
                for part in [
                    fields['Application Type'],
                    result.get('description')
                ]
                if part
            ])

        result['info_url'] = browser.url
        result['comment_url'] = ENQUIRY_URL
    finally:
        browser.back()

    return result


def get_pagination_links(browser):
    page_links = browser.find_by_xpath(".//tr[@class='pagerRow']//a")
    return [link["href"] for link in page_links]

import requests
import lxml.html
from collections import OrderedDict
from datetime import datetime
from morph_planningalerts import DevelopmentApplication
from util import AspJsLink
from urllib import quote

# NOTE: There doesn't seem to be a direct email address for application enquiries.
#   So, we'll just use their main "general" email.
ENQUIRE_EMAIL = "mailto:mail@noosa.qld.gov.au"


def get_application_links(page_url):
    """ This routine hunts down all the development application links,
        within the given page.

        Each of these links should be yielded back to the caller, or
        all returned at once in an iterable result (eg. list).
    """
    response = requests.get(page_url)
    content = lxml.html.fromstring(response.text)
    pages = get_pagination_links(page_url, content)
    finished = False

    applications = OrderedDict()

    # NOTE: We walk all the listed pages for links now,
    #   since we don't get to backtrack to a specific pagenation
    #   once we visit the detail page. The lists all share the same
    #   url, with page selection controlled by javascript form submits. :P
    while len(content) and not finished:
        links = content.xpath(
            "//tr[@class!='headerRow' and @class!='pagerRow']/td[1]/a"
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
            # Fetch the next page of application links
            next_page_link = pages.pop(0)
            response = next_page_link.click()
            content = lxml.html.fromstring(response)
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


def extract_application_details(application_url):
    """ Find all relevant development application information,
        from the details url we're given.

        The result should be one dictionary having the fields
        expected by a morph_planningalerts.DevelopmentApplication record.
    """
    response = requests.get(application_url)
    response.raise_for_status()
    content = lxml.html.fromstring(response.text)

    display_map = {
        u'Application Number': 'council_reference',
        u'Address': 'address',
        u'Description': 'description',
        u'Submitted Date': ('date_received', lambda d: datetime.strptime(d, '%d/%m/%Y').date()),
    }

    display_names = [
        element.text
        for element in content.xpath(
            "//tr[@class='normalRow' or @class='alternateRow']/td[1]"
        )
    ]
    field_values = [
        element.text
        for element in content.xpath(
            "//tr[@class='normalRow' or @class='alternateRow']/td[2]"
        )
    ]

    fields = dict(zip(display_names, field_values))

    result = {}
    for display_name, value in fields.items():
        display_name = display_name.strip() if display_name else None
        value = value.strip() if value else None

        if not display_name:
            # NOTE: Some fields contain links as their "name", which
            #   means that the td[1] we hunted for earlier gives us None.
            #   Those fields aren't the ones we're trying to scrape anyway,
            #   so... skip.
            continue

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

    if not 'council_reference' in result:
        raise ValueError("Failed to parse: " + application_url)

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

    result['info_url'] = application_url
    result['comment_url'] = "{0}?subject={1}".format(
        ENQUIRE_EMAIL,
        quote(
            "Development Application Enquiry: " + result['council_reference']
        )
    )
    return result


def get_pagination_links(current_url, page_tree):
    page_links = page_tree.xpath("//tr[@class='pagerRow']//a/@href")
    return [
        AspJsLink(current_url, page_tree, link)
        for link in page_links
    ]

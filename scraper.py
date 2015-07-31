import os
from splinter import Browser
from morph_planningalerts import DevelopmentApplication, MorphDatabase

from .scraperlib.local_knowledge import (
    get_application_links, extract_application_details
)

# Starting from the "Submitted this month" page
DEFAULT_START_URL = "https://noosa-eproperty.t1cloud.com/NOOEPRPROD/P1/eTrack/eTrackApplicationSearchResults.aspx?Field=S&Period=TM&r=P1.WEBGUEST&f=$P1.ETR.SEARCH.STM"


def get_agent(driver_name="phantomjs"):
    return Browser(driver_name)


def main(start_url, custom_agent=None):
    MorphDatabase.init()
    agent = custom_agent or get_agent()

    count_new = total = 0

    for application_url in get_application_links(agent, start_url):
        da_info = extract_application_details(agent, application_url)

        application, created = DevelopmentApplication.create_or_get(
            **da_info
        )

        total += 1

        if not created:
            print("Skipping {0.council_reference}".format(application))
        else:
            count_new += 1

    print("Added {0} records out of {1} processed.".format(count_new, total))


if __name__ == "__main__":
    with get_agent() as browser:
        main(
            start_url=os.environ.get('MORPH_START_URL', DEFAULT_START_URL),
            agent=browser
        )


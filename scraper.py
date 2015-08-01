import os
from splinter import Browser
from morph_planningalerts import DevelopmentApplication, MorphDatabase

from scraperlib.local_knowledge import (
    get_application_links, extract_application_details
)

# Starting from the "Submitted this month" page
DEFAULT_START_URL = "https://noosa-eproperty.t1cloud.com/NOOEPRPROD/P1/eTrack/eTrackApplicationSearchResults.aspx?Field=S&Period=TM&r=P1.WEBGUEST&f=$P1.ETR.SEARCH.STM"


# NOTE: There's a current issue with phantomjs where in some situations,
#   orphaned processes are left running after the ".quit()" method is called.
#   See the comments here:
#     https://github.com/SeleniumHQ/selenium/issues/767, and
#     https://github.com/detro/ghostdriver/issues/162#issuecomment-105762558
#
#   It sounds link, from those comments, that the problem is related to the
#   npm version of phantom. e.g.:
#     "It seems removing the npm version of phantom and building it eliminated the issue."
#
#   I believe on morph.io, the "built" phantom is in place, so I don't think
#   the issue is being seen there. But, if suddenly you begin running out of
#   memory, and have 6GB of zombie phantoms... you're probably hitting this
#   problem.
def get_agent(driver_name="phantomjs"):
    return Browser(driver_name)


def main(start_url, custom_agent=None):
    MorphDatabase.init()
    agent = custom_agent or get_agent()

    count_new = total = 0

    # Run in a with block. Ensures browser.quit()
    with agent as browser:
        for application_url in get_application_links(browser, start_url):

            if not application_url:
                # Skipped entry...
                total += 1
                continue

            da_info = extract_application_details(browser, application_url)

            application, created = DevelopmentApplication.get_or_create(
                **da_info
            )

            total += 1

            if not created:
                print("* Skipping {0.council_reference}".format(application))
            else:
                print("Saved {0.council_reference}".format(application))
                count_new += 1

    print("Added {0} records out of {1} processed.".format(count_new, total))


if __name__ == "__main__":
    main(
        start_url=os.environ.get('MORPH_START_URL', DEFAULT_START_URL)
    )


import os
from morph_planningalerts import DevelopmentApplication, MorphDatabase

from scraperlib.local_knowledge import (
    get_application_links, extract_application_details
)

# Starting from the "Submitted this month" page
DEFAULT_START_URL = "https://noo-web.t1cloud.com/T1PRDefault/WebApps/eProperty/P1/eTrack/eTrackApplicationSearchResults.aspx?Field=S&Period=TM&r=P1.WEBGUEST&f=$P1.ETR.SEARCH.STM"


def main(start_url):
    MorphDatabase.init()
    count_new = total = 0

    for application_url in get_application_links(start_url):

        if not application_url:
            # Skipped entry...
            total += 1
            continue

        da_info = extract_application_details(application_url)

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


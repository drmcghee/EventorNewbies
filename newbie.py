#!/usr/bin/env python3

import requests
import os
import sys
from lxml import etree

def EventorRequest(url):
    """ Eventor request
    """
    apikey =  os.environ.get('EventorAPIKey')
    if (apikey==None):
        #print("The eventor key will be read from the local directory file name eventorapikey.txt")
        with open("eventorapikey.txt") as f:
            apikey = f.read()

    response = requests.get(
        url=url,
        headers={
            'User-Agent': 'eventor-bot',
            'ApiKey': apikey
        },
    )
    
    if (response.status_code!=200):
        print("There was an error in the eventor request. Response was {0}".format(response.text) )

    # load the XML into lxml tree
    root = etree.fromstring(response.content)
    return root

class MinimalNewbie:
    """ Basic information for a newbie
    """
    def __init__(self, eventId, eventName, eventStart, competitorId, given, family, eventStatus):
        self.eventId = eventId
        self.eventName = eventName
        self.eventStart = eventStart
        self.competitorId = competitorId
        self.given = given
        self.family = family
        self.eventStatus = eventStatus

    def __iter__(self):
        for each in self.__dict__.keys():
            yield self.__getattribute__(each)


def GetEvents(dateStart, dateEnd, organisationIds):
    """ Get a list of events for the  search date range
    """
    print("Searching eventor for events between {0} and {1}".format(dateStart,dateEnd))
    url = "https://eventor.orienteering.asn.au/api/events?fromDate={0}&toDate={1}&OrganisationIds={2}".format(dateStart, dateEnd, organisationIds)
    root = EventorRequest(url)

    # find event ids (and names) from all events returns
    xpath = "/EventList/Event/EventId"
    eventids = root.xpath(xpath)
    eventCount = len(eventids)
    print("Found {0} events".format(eventCount))

    if (eventCount==0):
        print("Exiting - No events found for date range {0} to {1}".format(dateStart, dateEnd))
    else:
        # create a list of event locations
        newbieData = []

        # for each event add any newbies found for that event
        for eventid in eventids:
            newbieData = newbieData + GetNewbies(eventid.text)

        # convert to CSV
        print("Writing to CSV file")
        import csv
        with open("newbies-{0}-{1}.csv".format(dateStart, dateEnd), "w", newline='') as f:
            out = csv.writer(f)
            out.writerows(newbieData)
        print("Complete!")


def GetNewbies(eventId):
    """ Get a list of newbies (those with no organisation) for an event based on a search date range
    """
    print("Searching eventor results for event {0}".format(eventId))
    url = "https://eventor.orienteering.asn.au/api/results/event?eventid={0}".format(eventId)
    root = EventorRequest(url)

    # get event name
    xpath = "/ResultList/Event/Name"
    eventNameResults = root.xpath(xpath)
    eventName = eventNameResults[0].text

    # get event date
    xpath = "/ResultList/Event/StartDate"
    eventStartResults = root.xpath(xpath)
    eventStart = eventStartResults[0][0].text

    # find newbies
    xpath = "/ResultList/ClassResult/PersonResult[not(Organisation)]"
    newbieResults = root.xpath(xpath)
    newbieCount = len(newbieResults)
    print("{0} - {1} ".format(eventStart, eventName))
    print("Found {0} newbie results".format(newbieCount))

    # create a list of event locations
    newbies = []

    # grab the id, given name, family name and the result
    for personResult in newbieResults:
        competitorId = "Unknown"
        given = ""
        family = ""
        status = "No event competitor status found"

        for resultChild in personResult:
            if (resultChild.tag=='Person'):
                for personChild in resultChild:
                    if (personChild.tag=='PersonId'):
                        # get value of id if available
                        if (personChild.text!=None):
                            competitorId = personChild.text
                    if (personChild.tag=='PersonName'):
                        for personName in personChild:
                            if (personName.tag=="Family"):
                                family = personName.text
                            if (personName.tag=="Given"):
                                given = personName.text
            if (resultChild.tag=='Result'):
                for resultElement in resultChild:
                    if (resultElement.tag=='CompetitorStatus'):
                        status =resultElement.attrib["value"]
    
        # create a newbie
        newbie = MinimalNewbie(eventId, eventName, eventStart, competitorId, given, family, status)
        newbies.append(newbie) 
    return newbies
    
if __name__ == '__main__':
    #app.run(debug=True,host='0.0.0.0',port=80)
    sys.path.insert(0, os.path.abspath('..'))

    import argparse

    parser = argparse.ArgumentParser(description='Arguments for eventor newbies')
    parser.add_argument('startDate', action="store")
    parser.add_argument('endDate', action="store")
    parser.add_argument('organisationIds', action="store")

    args = parser.parse_args()
    GetEvents(args.startDate, args.endDate, args.organisationIds)
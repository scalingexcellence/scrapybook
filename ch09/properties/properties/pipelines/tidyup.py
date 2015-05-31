from datetime import datetime


class TidyUp(object):
    """A pipeline that does some basic post-processing"""

    def process_item(self, item, spider):
        """
        Pipeline's main method. Formats the date as a string.
        """

        item['date'] = map(datetime.isoformat, item['date'])

        return item

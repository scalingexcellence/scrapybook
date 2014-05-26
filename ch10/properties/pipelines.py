import re

class PricePipeline(object):
    def process_item(self, item, spider):
        price = item['price']
        if not price:
            raise DropItem("%s doesn't have a price" % item['url'])

        # If price per month then divide by 4.3 to convert to per week
        norm = 4.3 if item['price'].endswith("pm") else 1
        price = price.replace(",", "")  # remove commas e.g. 1,234 -> 1234
        price = re.sub("\..*", "", price)  # remove any decimal e.g. 3.21 -> 3
        price = re.sub("[^0-9]", "", price)  # remove non-numeric characters
        price = float(price) / norm  # convert to float and normalize
        item['price'] = price

        return item

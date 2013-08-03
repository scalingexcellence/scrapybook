// Use: mongo --quiet scrapy_lon loctions.js > locations.txt

db.appartments.mapReduce(
	function() {
		if (this.geo_addr) { emit(this.address, 1); }
	},
	function(key, hits) {
		return Array.sum(hits);
	},
	{
		out: "hits"
	}
)

cursor = db.hits.find().sort({value:-1}).limit(100);
while(cursor.hasNext()){
    print(cursor.next()._id);
}

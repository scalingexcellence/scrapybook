// Use: mongo --quiet scrapy_lon titles.js > titles.txt

db.appartments.mapReduce(
	function() {
                words = this.title.toLowerCase().split(/[^a-zA-Z]+/).filter(function(n){return n})
		for (i in words) emit(words[i], 1);
	},
	function(key, hits) {
		return Array.sum(hits);
	},
	{
		out: "hits"
	}
)

cursor = db.hits.find().sort({value:-1}).limit(1000);
while(cursor.hasNext()){
    print(cursor.next()._id);
}


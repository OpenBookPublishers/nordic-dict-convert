
output.xml: nordic_extract.py live.db
	./nordic_extract.py > $@

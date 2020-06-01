from elasticsearch import Elasticsearch
from elasticsearch.exceptions import RequestError
import os
import pickle
from tqdm import tqdm

INDEX_NAME = "hw3"
cloud_id = 'CS6200-2:dXMtZWFzdDQuZ2NwLmVsYXN0aWMtY2xvdWQuY29tJDgyYmYzNzcxZTg2NTQwMTlhNzU1OTNiMGJlOWZmOWQyJGMzNTRkZGIzZjgxZDQ0MWM4OWE2ZmE2YTExOGE3NTEz'
es = Elasticsearch(request_timeout=10000, timeout=10000, cloud_id=cloud_id,
                   http_auth=('elastic', 'TdCF4eVax9f8dIXulNqcMMHr'))


def merge(inlinks, url, outlinks, body=None, head=None):
    try:
        query_body = {
            "query": {
                "match": {
                    "_id": url
                }
            }
        }
        # print("Merging to the elastic search cloud instance")
        hits = es.search(index=INDEX_NAME, body=query_body)
        if hits['hits']['total']['value'] != 0:
            es.update(index=INDEX_NAME, id=url,
                      body={
                          "script": {
                              "source": "ctx._source.inlinks.addAll(params.inlinks); "
                                        "ctx._source.inlinks=ctx._source.inlinks.stream().distinct().sorted().collect("
                                        "Collectors.toList());ctx._source.outlinks.addAll(params.outlinks); "
                                        "ctx._source.outlinks=ctx._source.outlinks.stream().distinct().sorted().collect("
                                        "Collectors.toList())",
                              "lang": "painless",
                              "params": {
                                  "inlinks": inlinks,
                                  "outlinks": outlinks
                              }
                          }
                      })
        else:
            insert_body = {
                'text': body,
                'outlinks': outlinks,
                'inlinks': inlinks,
                'head': head
            }
            es.index(index=INDEX_NAME, body=insert_body, id=url)
        # print("Merged", url)
    except RequestError:
        pass


def parseFile(file_content):
    while '<DOC>' in file_content:
        doc_content = file_content[:file_content.find('</DOC>')]
        docno_start = doc_content.find('<DOCNO>') + len('<DOCNO>')
        docno_end = doc_content.find('</DOCNO>')
        docno = doc_content[docno_start:docno_end].strip()

        head_start = doc_content.find('<HEAD>') + len('<HEAD>')
        head_end = doc_content.find('</HEAD>')
        head = doc_content[head_start:head_end].strip()

        text_start = doc_content.find('<TEXT>') + len("<TEXT>")
        text_end = doc_content.find("</TEXT>")
        text = doc_content[text_start:text_end].strip() + "\n"

        ol_start = doc_content.find('<OUTLINKS>') + len("<OUTLINKS>")
        ol_end = doc_content.find("</OUTLINKS>")
        ol = doc_content[ol_start:ol_end].strip() + "\n"
        ol = ol[1:-2].split(', ')
        for i, link in enumerate(ol):
            ol[i] = ol[i][1:-2]

        ol = list(filter(None, ol))
        doc_content = doc_content[ol_end + len("</OUTLINKS>"):]
        if docno in urls:
            il = inlink_dict[docno]
        else:
            il = []

        print(il, "\n")
        # merge(il, docno, ol, text.strip(), head)
        file_content = file_content[file_content.find('</DOC>') + len("</DOC>"):]


f = open("./inlinks.txt", "r+b")
inlink_dict = pickle.load(f)
urls = inlink_dict.keys()

for file in tqdm(os.listdir('/home/arjun/Desktop/dumps/')):
    with open(os.path.join('/home/arjun/Desktop/dumps/', file), "r", encoding="ISO-8859-1") as f:
        parseFile(f.read())

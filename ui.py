import csv
import tkinter as tk
import webbrowser
from itertools import zip_longest

from elasticsearch import Elasticsearch
import operator

INDEX_NAME = "hw3"
cloud_id = 'CS6200-2:dXMtZWFzdDQuZ2NwLmVsYXN0aWMtY2xvdWQuY29tJDgyYmYzNzcxZTg2NTQwMTlhNzU1OTNiMGJlOWZmOWQyJGM' + \
           'zNTRkZGIzZjgxZDQ0MWM4OWE2ZmE2YTExOGE3NTEz'
es = Elasticsearch(request_timeout=10000, timeout=10000, cloud_id=cloud_id,
                   http_auth=('elastic', 'TdCF4eVax9f8dIXulNqcMMHr'))


class VerticalSearch:

    def __init__(self):

        window = tk.Tk()
        window.title("Barack Obama Web Crawler")
        window.geometry("500x100")
        # create the input boxes.
        tk.Label(window, text="Welcome to our Web Crawler").pack()
        tk.Label(window, text="Enter your query:").pack()

        # for taking inputs
        self.inputQuery = tk.StringVar()
        tk.Entry(window, textvariable=self.inputQuery, justify=tk.RIGHT).pack()

        # create the button
        tk.Button(window, text="Search", command=self.fetch_results).pack()

        self.results = tk.StringVar()
        tk.Label(window, textvariable=self.results, text="Results:").pack()

        window.mainloop()

    def fetch_results(self):
        query = self.inputQuery.get()
        a = self.get_relevant_documents(query)
        print(a)

        with open('qrel.csv', 'a') as f:
            writer = csv.writer(f)
            for val in a[:200]:
                writer.writerow([val])
        # app = ListApp(a)
        # app.mainloop()
        # self.results.set(self.inputQuery.get())

    @staticmethod
    def get_relevant_documents(query):
        doc_list = []
        doc_dict = {}
        query = query.strip()
        terms = []
        raw_terms = query.split(" ")
        for t in raw_terms:
            t = t.strip()
            terms.append(t)
        result = es.search(index=INDEX_NAME, size=1000, body={'query': {'match': {'text': ' '.join(terms)}}})["hits"]["hits"]
        for entry in result:
            doc_dict[entry['_id']] = entry['_score']
        sorted_doc_dict = dict(sorted(doc_dict.items(), key=operator.itemgetter(1), reverse=True))
        counter = 0

        urls = sorted_doc_dict.keys()
        for url in urls:
            counter = counter + 1
            doc_list.append(url)
            if counter == 1000:
                break
        return doc_list


class ListApp(tk.Tk):
    def __init__(self, l):
        super().__init__()
        self.print_btn = tk.Button(self, text="Open URL", command=self.print_selection)
        self.frame = tk.Frame(self)
        self.scroll_v = tk.Scrollbar(self.frame, orient=tk.VERTICAL)
        self.scroll_h = tk.Scrollbar(self.frame, orient=tk.HORIZONTAL)
        self.list = tk.Listbox(self.frame, yscrollcommand=self.scroll_v.set, xscrollcommand=self.scroll_h.set)
        self.list.insert(0, *l)
        self.scroll_v.config(command=self.list.yview)
        self.scroll_h.config(command=self.list.xview)
        self.frame.pack()
        self.list.pack(side=tk.LEFT)
        self.scroll_v.pack(side=tk.LEFT, fill=tk.Y)
        self.scroll_h.pack(side=tk.BOTTOM, fill=tk.X)
        self.print_btn.pack()

    def print_selection(self):
        selection = self.list.curselection()
        str_url = [self.list.get(i) for i in selection]
        webbrowser.open(str_url[0], new=2)


VerticalSearch()

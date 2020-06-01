import itertools
from collections import deque
from collections import OrderedDict
import constants

import html_parser
import time
import operator
import os
import pickle
import socket
import signal
import robot_parser


class TimeoutException(Exception):
    pass


def timeout_handler():
    raise TimeoutException


class MyCrawler:
    def __init__(self, flag):
        if not flag:
            self.frontier = deque()
            self.window_start = 0
            self.wave_graph = OrderedDict()
            self.document_content = ""
            for seed in constants.SEED_URLS:
                self.frontier.append(seed)
            self.wave_graph[1] = constants.SEED_URLS
            self.anchor_text_dict = {}
            self.in_links_dict = {}
            self.in_links_count = {}
        else:
            recovery_f = open("recovery.txt", "r+b")
            recovery_dict = pickle.load(recovery_f)
            recovery_f.close()
            self.frontier = recovery_dict["frontier"]
            self.window_start = recovery_dict["window_start"]
            self.wave_graph = recovery_dict["wave_graph"]
            self.document_content = recovery_dict["document_content"]
            self.anchor_text_dict = recovery_dict["anchor_text_dict"]
            self.in_links_dict = recovery_dict["in_links_dict"]
            self.in_links_count = recovery_dict["in_links_count"]

    def crawl(self, limit):
        signal.signal(signal.SIGALRM, timeout_handler)
        while self.window_start <= limit:
            try:
                signal.alarm(60)
                socket.create_connection(("www.google.com", 80))
                current_url = self.frontier[self.window_start]
                self.window_start += 1
                parent_wave = self.update_wave_graph(current_url)
                if len(self.in_links_dict) >= 500:
                    self.write_in_links()
                    self.in_links_dict.clear()
                if current_url not in list(itertools.islice(self.frontier, self.window_start - 1)):
                    rp_obj = robot_parser.RobotParser()
                    robot_data = rp_obj.get_timeout(current_url)
                    if robot_data[0] is False:
                        continue
                    sleep_time = 1 if robot_data[1] is None else robot_data[1]
                    result = html_parser.HTMLParser.parse_html(current_url)
                    if result is None:
                        continue
                    if result["content"] is "":
                        continue
                    if self.check_bad_content(result['content']):
                        continue
                    self.document_content += self.create_document(current_url, result) + "\n"
                    if len(self.window_start) % 50 == 0:
                        self.write_document()
                        self.document_content = ""
                    print(self.window_start, ". Processed: ", current_url)
                    time.sleep(sleep_time)
                    self.update_anchor_dict(result['out_links'])
                    out_links = result['out_links'].keys()
                    out_links = self.remove_bad_links(out_links)
                    self.add_wave(out_links, parent_wave)
                    for out_link in out_links:
                        if out_link not in self.in_links_dict:
                            temp = [current_url]
                            self.in_links_dict[out_link] = temp
                            self.in_links_count[out_link] = 1
                        else:
                            temp = self.in_links_dict[out_link]
                            temp.append(current_url)
                            self.in_links_dict[out_link] = temp
                            self.in_links_count[out_link] += 1
                        self.frontier.append(out_link)
                    if len(out_links) >= 250:
                        self.score_frontier()
                    if self.window_start % 100 == 0:
                        self.save_state()
                else:
                    self.in_links_count[current_url] += 1
                    continue
            except TimeoutException:
                self.window_start += 1
                continue
            except (KeyboardInterrupt or Exception) as e:
                print(str(e))
                self.save_state()
                break

    def update_anchor_dict(self, a_dict):
        for key in a_dict:
            if key in self.anchor_text_dict():
                self.anchor_text_dict[key].append(a_dict[key])
            else:
                self.anchor_text_dict[key] = deque()
                self.anchor_text_dict[key].append(a_dict[key])

    def add_wave(self, out_links, parent_wave):
        waves = self.wave_graph.keys()
        child_wave = parent_wave + 1
        if child_wave not in waves:
            self.wave_graph[child_wave] = out_links
        else:
            self.wave_graph[child_wave].extend(out_links)

    def update_wave_graph(self, visited_url):
        waves = self.wave_graph.keys()
        for wave in waves:
            if visited_url in self.wave_graph[wave]:
                wave_list = self.wave_graph[wave]
                wave_list.remove(visited_url)
                self.wave_graph[wave] = wave_list
                if len(wave_list) == 0:
                    del (self.wave_graph[wave])
                return wave

    def score_frontier(self):
        wave_list = []
        start_wave = next(iter(self.wave_graph.items()))[0]
        end_wave = start_wave + 2
        waves = self.wave_graph.keys()
        for i in range(start_wave, end_wave + 1):
            if i in waves:
                wave_list.extend(self.wave_graph[i])
        prioritized_urls = self.score_urls(wave_list)
        for i in range(end_wave + 1, len(self.wave_graph)):
            if i in waves:
                prioritized_urls.extend(self.wave_graph[i])
        temp_queue = deque(prioritized_urls)
        self.frontier = list(itertools.islice(self.frontier, self.window_start - 1))
        self.frontier.extend(temp_queue)

    def score_urls(self, wave_list):
        url_score_dict = {}
        for url in wave_list:
            in_link_count = self.in_links_count[url]
            keyword_value = 0
            for keyword in constants.KEYWORDS:
                if keyword.lower() in url.lower():
                    keyword_value += constants.URL_KEYWORD_SCORE_DICT[keyword]
                if keyword in self.anchor_text_dict[url].popleft():
                    keyword_value += constants.ANCHOR_TEXT_KEYWORD_DICT[keyword]
            score = in_link_count + keyword_value
            url_score_dict[url] = score
        sorted_url_content_dict = dict(sorted(url_score_dict.items(), key=operator.itemgetter(1), reverse=True))
        prioritized_urls = sorted_url_content_dict.keys()
        return prioritized_urls

    def save_state(self):
        variable_dict = {"frontier": self.frontier, "in_links_dict": self.in_links_dict,
                         "window_start": self.window_start,
                         "wave_graph": self.wave_graph, "document_content": self.document_content,
                         "anchor_text_dict": self.anchor_text_dict, "in_links_count": self.in_links_count}
        if os.path.isfile('recovery.txt'):
            os.remove('recovery.txt')
        recovery_file = open("recovery.txt", "a+b")
        pickle.dump(variable_dict, recovery_file)
        recovery_file.close()

    @staticmethod
    def create_document(url, result):
        doc = "<DOC>\n"
        doc_no = "<DOCNO>" + url + "</DOCNO>\n"
        head = "<HEAD>" + result['title'] + "</HEAD>\n"
        text = "<TEXT>\n" + result['content'] + "\n</TEXT>\n"
        out_links = "<OUTLINKS>" + str(result['out_links']) + "</OUTLINKS>\n"
        end_doc = "</DOC>"
        document = doc + doc_no + head + text + out_links + end_doc
        return document

    def write_document(self):
        output_dump = open("./dumps/ap" + str(self.window_start / 50) + ".txt", "a")
        output_dump.write(self.document_content)
        output_dump.close()

    def write_in_links(self):
        if os.path.isfile('inlinks.txt'):
            in_link_file = open("inlinks.txt", "r+b")
            temp_dict = pickle.load(in_link_file)
            keys = self.in_links_dict.keys()
            temp_keys = temp_dict.keys()
            for k in keys:
                if k in temp_keys:
                    parents = temp_dict[k]
                    parents.extend(self.in_links_dict[k])
                    temp_dict[k] = parents
                else:
                    temp_dict[k] = self.in_links_dict[k]
            self.in_links_dict = temp_dict
            in_link_file.close()
            os.remove("inlinks.txt")
        in_link_file = open("inlinks.txt", "a+b")
        pickle.dump(self.in_links_dict, in_link_file)
        in_link_file.close()

    @staticmethod
    def check_bad_content(content):
        for bad_content in constants.BAD_CONTENT:
            if bad_content in content:
                return True
        return False

    @staticmethod
    def remove_bad_links(links):
        good_links = []
        for link in links:
            flag = True
            for links in constants.BAD_LINKS:
                if links.lower() in link.lower():
                    flag = False
                    break
            if flag:
                good_links.append(link)
        return good_links


if __name__ == '__main__':
    restart_flag = False
    c = MyCrawler(restart_flag)
    c.crawl(constants.WEB_PAGES_TO_CRAWL)

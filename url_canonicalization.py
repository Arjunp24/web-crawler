#  Copyright (C) 2020  Arvind Mukund <armu30@gmail.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

import re


class URLCanonicalization:

    @staticmethod
    def clean_url(url, text, domain):
        """
        1. Convert the scheme and host to lower case:
           HTTP://www.Example.com/SomeFile.html → http://www.example.com/somefile.html
        2. Remove port 80 from http URLs, and port 443 from HTTPS URLs:
           http://www.example.com:80 → http://www.example.com
        3. Make relative URLs absolute: if you crawl http://www.example.com/a/b.html and find the URL ../c.html,
           it should canonicalize to http://www.example.com/c.html.
        4. Remove the fragment, which begins with #:
           http://www.example.com/a.html#anything → http://www.example.com/a.html
        5. Remove duplicate slashes: http://www.example.com//a.html → http://www.example.com/a.html    
        """

        # APPEND URL WITH DOMAIN IF WE HAVE STARTING AS /
        url = URLCanonicalization.test_for_no_domain(url, domain)

        # Lcase the domain name
        url = URLCanonicalization.lower_case_domain(url)

        # Remove ports
        url = URLCanonicalization.test_for_default_ports(url)

        # Remove hashtags
        url = URLCanonicalization.test_for_url_same_page(url)

        # Remove double slash
        url = URLCanonicalization.test_for_double_slash(url)

        # Remove path traversal to base page.
        url = URLCanonicalization.test_path_traversal(url)

        return url, text

    @staticmethod
    def test_path_traversal(url):
        if "../" in url:
            split = url.split('/')
            count = 0
            for x in split:
                if ".." in x:
                    count += 1
            if len(split) / 2 - 2 < count:
                return url
            i = 0
            while i < len(split):
                if split[i] == '..':
                    split.remove(split[i])
                    split.remove(split[i - 1])
                    i -= 1
                    continue
                i += 1
            return '/'.join(x for x in split)
        else:
            return url

    @staticmethod
    def reverse(s):
        if len(s) == 0:
            return s
        else:
            return URLCanonicalization.reverse(s[1:]) + s[0]

    @staticmethod
    def test_for_double_slash(url):
        temp = re.sub('//', '/', url)
        return temp.replace(':/', '://')

    @staticmethod
    def test_for_url_same_page(url):
        if "#" in url:
            hash_index = url.find("#")
            url = url[0:hash_index]
        return url

    @staticmethod
    def test_for_default_ports(url):
        if url.startswith("http") and url.endswith(":80"):
            url = url[:-3]
        if url.startswith("https") and url.endswith(":443"):
            url = url[:-4]
        return url

    @staticmethod
    def test_for_no_domain(url, domain):
        temp = url
        if temp.startswith("/"):
            temp = domain + temp
        return temp

    @staticmethod
    def lower_case_domain(url):
        x = [y for y in url]
        index1 = 0
        slashes = 0
        while index1 < len(url):
            if x[index1] == '/':
                if slashes + 1 == 3:
                    break
                slashes += 1
            else:
                x[index1] = x[index1].lower()
            index1 += 1

        return ''.join(xy for xy in x)

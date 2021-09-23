#  coding: utf-8 
import socketserver
import os
import urllib.request
from datetime import date

from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime


# Copyright 2013 Abram Hindle, Eddie Antonio Santos
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# Furthermore it is derived from the Python documentation examples thus
# some of the code is Copyright © 2001-2013 Python Software
# Foundation; All Rights Reserved
#
# http://docs.python.org/2/library/socketserver.html
#
# run: python freetests.py

# try: curl -v -X GET http://127.0.0.1:8080/


class MyWebServer(socketserver.BaseRequestHandler):

    def handle(self):
        #code for how to get the date in the correct format from https://stackoverflow.com/questions/225086/rfc-1123-date-representation-in-python
        unformatted_dateime = datetime.now()
        stamp = mktime(unformatted_dateime.timetuple())
        todays_date = (format_date_time(stamp))
        decoded_response = ""
        while True:
            one_byte = self.request.recv(1).decode()
            decoded_response += one_byte
            if "\r\n\r\n" in decoded_response:
                break

        #print ("Got a request of: %s\n" % self.data) #not needed for my implementation but very helpful for debugging!
        if (decoded_response == ""):
            #got the request b'' so do nothing
            self.request.close()
            return

        #used https://stackoverflow.com/questions/29643544/python-a-bytes-like-object-is-required-not-str for the idea of splitting a string using split
        decoded_response_split = (decoded_response.split(" "))

        request_type = decoded_response_split[0] #get everything from the request up to the first space ie. the request type
        if (request_type != "GET"):
            #405 error for any request type other than GET
            self.request.send(bytearray("HTTP/1.1 405 Method Not Allowed\r\n",'utf-8'))
            self.request.send(bytearray("Date: "+str(date)+"\r\n",'utf-8'))
            self.request.send(bytearray("Connection: close\r\n\r\n",'utf-8'))
            self.request.close()
            return
        base_file_path = decoded_response_split[1] #the basic path requested without any changes
        file_path = "www"+base_file_path #automatically add in the www as per the specifications
        
        file_path = urllib.request.url2pathname(file_path) #using https://docs.python.org/3/library/urllib.request.html in order to parse the file path
        #for example transforming %20 into spaces
        
        #the idea for getting the relative path comes from https://www.geeksforgeeks.org/python-os-path-relpath-method/
        file_relative_path = os.path.relpath(file_path)

        #idea on how to get string length https://www.educative.io/edpresso/how-to-find-the-length-of-a-string-in-python
        #just makes sure that the relative path is at least 3 so the next if does not fail
        if(len(file_relative_path) < 3):
            self.request.send(bytearray("HTTP/1.1 404 Not Found\r\n",'utf-8'))
            self.request.send(bytearray("Date: "+str(date)+"\r\n",'utf-8'))
            self.request.send(bytearray("Connection: close\r\n\r\n",'utf-8'))
            self.request.close()
            return
        if(file_relative_path[0:3] != "www"):
            self.request.send(bytearray("HTTP/1.1 404 Not Found\r\n",'utf-8'))
            self.request.send(bytearray("Date: "+str(date)+"\r\n",'utf-8'))
            self.request.send(bytearray("Connection: close\r\n\r\n",'utf-8'))
            self.request.close()
            return

        #used https://reactgo.com/python-remove-first-last-character-string/ for the idea to use [-1] for the last character in the string
        if (file_path[-1] == '/'): #since this is a directory add in index.html as per the specifications
            file_path = file_path + "index.html"

        #used https://www.thepythoncode.com/article/send-receive-files-using-sockets-python extensively for the idea of opening files with open
        # as well as reading bytes from the file using a buffer size and getting the file size and the use of decode
        try:
            with open(file_path, "rb") as f:
                file_size = (os.path.getsize(file_path))
                bytes_read = f.read(file_size) #if we can open the file read its contents
        except: #can't open the file therefore it may be a directory or trying to get a file that does not exist
            path = file_path+ "/"
            #used https://careerkarma.com/blog/python-check-if-file-exists/ to figure out how to check if a path exists ie the line os.path.isdir(path)
            if (os.path.isdir(path)):
                updated_path = "http://127.0.0.1:8080" + base_file_path + "/" #make the change so that the correct directory is returned in the 301 response
                #used https://stackoverflow.com/questions/21153262/sending-html-through-python-socket-server for the idea to use the .send and adding in the Content-Type portion
                self.request.send(bytearray("HTTP/1.1 301 Moved Permanently\r\n",'utf-8'))
                self.request.send(bytearray("Date: "+str(todays_date)+"\r\n",'utf-8'))
                self.request.send(bytearray("URL: "+updated_path+" \r\n",'utf-8'))
                self.request.send(bytearray("Connection: close\r\n\r\n",'utf-8'))
                self.request.close()
                return
            else: #not a valid file and not a valid directory = 404 error
                self.request.send(bytearray("HTTP/1.1 404 Not Found\r\n",'utf-8'))
                self.request.send(bytearray("Date: "+str(todays_date)+"\r\n",'utf-8'))
                self.request.send(bytearray("Connection: close\r\n\r\n",'utf-8'))
                self.request.close()
                return
        

        extension = os.path.splitext(file_path)[1] #used https://stackoverflow.com/questions/4776924/how-to-safely-get-the-file-extension-from-a-url to
        #get the extension from the filepath
        self.request.send(bytearray("HTTP/1.1 200 OK\r\n",'utf-8'))
        if (extension == ".html"):
            self.request.send(bytearray("Content-Type: text/html\r\n",'utf-8')) #make sure content type aligns with information we are sending back
        elif (extension == ".css"):
            self.request.send(bytearray("Content-Type: text/css\r\n",'utf-8')) #make sure content type aligns with information we are sending back

        else: #use general mime type which I got from https://stackoverflow.com/questions/20163864/what-mime-type-to-use-as-general-purpose
            self.request.send(bytearray("Content-Type: application/octet-stream\r\n",'utf-8'))
        self.request.send(bytearray("Date: "+str(todays_date)+"\r\n",'utf-8'))
        self.request.send(bytearray("Connection: close\r\n",'utf-8'))
        self.request.send(bytearray("Content-Length: "+str(file_size)+"\r\n\r\n",'utf-8'))
        self.request.send(bytes_read)
        self.request.close()
        

if __name__ == "__main__":
    HOST, PORT = "localhost", 8080

    socketserver.TCPServer.allow_reuse_address = True
    # Create the server, binding to localhost on port 8080
    server = socketserver.TCPServer((HOST, PORT), MyWebServer)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
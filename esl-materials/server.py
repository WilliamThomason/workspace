import http.server, socketserver, os
print("CWD before:", os.getcwd())
os.chdir(r'C:\Users\irieb\Documents\William's Projects\workspace\esl-materials')
print("CWD after:", os.getcwd())
print("Files:", os.listdir('.')[:5])
handler = http.server.SimpleHTTPRequestHandler
with socketserver.TCPServer(('', 8090), handler) as httpd:
    print('Serving on port 8090')
    httpd.serve_forever()

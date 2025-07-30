from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import argparse
import urllib.parse

from transformers import AutoModelForCausalLM, AutoTokenizer

class HTTPServerWithModel(HTTPServer):
    def __init__(self, server_address, handler, model, tokenizer):
        super().__init__(server_address, handler)
        self.model = model
        self.tokenizer = tokenizer

class ModelResponseHandler(BaseHTTPRequestHandler):
    def get_response(self, input_query):
        model = self.server.model
        tokenizer = self.server.tokenizer
        processed_input_query = tokenizer(input_query, return_tensors="pt").to("cuda:0")
        output = model.generate(**processed_input_query, max_length=1024, num_return_sequences=1)
        return tokenizer.batch_decode(output, skip_special_tokens=True)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')

        if "application/json" in self.headers['Content-Type']:
            try:
                data = json.loads(post_data)
            except:
                self.send_error(400, "Invalid JSON")
                return
        elif "application/x-www-form-urlencoded" in self.headers['Content-Type']:
            data = urllib.parse.parse_qs(post_data)
        else:
            self.send_error(400, "Unsupported Content-Type")
            return
        
        if "query" not in data:
            self.send_error(400, "Missing 'query' parameter")
            return
        if not isinstance(data['query'], str):
            self.send_error(400, "Invalid 'query' parameter")
            return
        
        response = self.get_response(data['query'])
        print(response[0])
        response = {"data": response[0]}
        response = json.dumps(response)

        self.send_response(200)
        
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))


def run(args):
    model = AutoModelForCausalLM.from_pretrained(args.model_path_or_name, device_map="cuda:0")
    print("Load model done.")
    tokenizer=None
    tokenizer = AutoTokenizer.from_pretrained(args.model_path_or_name, device_map="cuda:0")
    print("Load tokenizer done.")
    server_address = (args.addr, args.port)
    httpd = HTTPServerWithModel(server_address, ModelResponseHandler, model, tokenizer)
    print("Server started on port", args.port)
    httpd.serve_forever()
    print("Server stopped")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", "-p", default=8000, type=int, help="Port to listen on")
    parser.add_argument("--addr", "-a", default="127.0.0.1", type=str, help="Address to listen on")
    parser.add_argument("--model_path_or_name", "-m", default=os.path.join(".", "Qwen2-0.5B"), type=str)
    args = parser.parse_args()

    run(args)
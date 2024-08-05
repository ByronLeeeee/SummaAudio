import sys
import os
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# from scripts import ollama_scripts

import ollama

from ollama import Client

# client = Client(host="http://localhost:11434")

print(ollama.generate(host="http://localhost:11434",model="qwen2",prompt="hello world"))
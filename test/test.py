import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.modelscope_scripts import recognition,organise_recognition
# from scripts import ollama_scripts

r = recognition('https://isv-data.oss-cn-hangzhou.aliyuncs.com/ics/MaaS/ASR/test_audio/asr_speaker_demo.wav',
            'iic/speech_paraformer-large-vad-punc-spk_asr_nat-zh-cn',
            'v2.0.4',
            'iic/speech_fsmn_vad_zh-cn-16k-common-pytorch',
            "v2.0.4",
            'iic/punc_ct-transformer_cn-en-common-vocab471067-large',
            "v2.0.4")

f,o =organise_recognition(r)

print(f)
print(o)
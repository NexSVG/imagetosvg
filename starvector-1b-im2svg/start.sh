#!/bin/bash

bash -c "$SSH_TUNNEL_CMD_1" &

echo "SSH tunnel started, PID: $SSH_PID"
python -m starvector.serve.vllm_api_gradio.controller --host 0.0.0.0 --port 10000 &
python -m starvector.serve.vllm_api_gradio.model_worker --host 0.0.0.0 --controller http://localhost:10000 --port 40000 --worker http://localhost:40000 --model-name /home/agent_h/data/starvector-1b-im2svg --vllm-base-url http://localhost:8000 &
python -m starvector.serve.vllm_api_gradio.gradio_web_server --controller http://localhost:10000 --model-list-mode reload --port 7860

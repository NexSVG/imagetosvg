"""
This module defines a self-contained StarVector model with support for remote code loading.
"""

import os
import torch
import torch.nn as nn
from transformers import PreTrainedModel, PretrainedConfig
from typing import Optional, Union, List
from abc import ABC, abstractmethod

# Import components - these will be included in the HF repo
from .starvector.image_encoder import ImageEncoder
from .starvector.adapter import Adapter

# === Model Configuration ===

class StarVectorConfig(PretrainedConfig):
    model_type = "starvector"

    def __init__(
        self,
        starcoder_model_name: str = "bigcode/starcoderbase-1b",
        image_encoder_type: str = "clip",
        adapter_norm: str = "layer_norm",
        image_size: int = 224,
        max_length: int = 8192,
        max_length_train: int = 8192,
        use_flash_attn: bool = True,
        use_cache: bool = True,
        num_attention_heads: int = 16,
        num_hidden_layers: int = 24,
        vocab_size: int = 49152,
        hidden_size: int = 2048,
        num_kv_heads: int = 4,
        torch_dtype: str = "bfloat16",
        **kwargs,
    ):
        # Initialize the parent config first
        super().__init__(**kwargs)
        self.starcoder_model_name = starcoder_model_name
        self.image_encoder_type = image_encoder_type
        self.adapter_norm = adapter_norm
        self.image_size = image_size
        self.max_length = max_length
        self.max_length_train = max_length_train
        self.use_flash_attn = use_flash_attn
        self.use_cache = use_cache
        self.num_attention_heads = num_attention_heads
        self.num_hidden_layers = num_hidden_layers
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size
        self.num_kv_heads = num_kv_heads
        self.torch_dtype = torch_dtype

# === Base Model Classes ===

class StarVectorBase(nn.Module, ABC):
    def __init__(self, config, **kwargs):
        super().__init__()
        self.task = kwargs.get('task', 'im2svg')
        self.model_precision = kwargs.get('model_precision', config.torch_dtype)
        
        # Instantiate the SVG transformer using the abstract method.
        self.svg_transformer = self._get_svg_transformer(config, **kwargs)
        
        if self.use_image_encoder():
            self.image_encoder = ImageEncoder(config, **kwargs)
            self.image_projection = self.get_adapter(config, **kwargs).to(dtype=self.model_precision)
        else:
            self.query_length = 0
            
        self.max_length = config.max_length_train - getattr(self, "query_length", 0) - 4  
        self.train_image_encoder = kwargs.get('train_image_encoder', False)
        self.train_LLM = kwargs.get('train_LLM', False)
        
        self._freeze_parameters(self.train_image_encoder, self.train_LLM)

    @abstractmethod
    def _get_svg_transformer(self, config, **kwargs):
        """Get SVG transformer model - implementation differs between versions"""
        pass

    def _freeze_parameters(self, train_image_encoder, train_LLM):
        if self.use_image_encoder():
            for _, param in self.image_encoder.named_parameters():
                param.requires_grad = train_image_encoder
            for _, param in self.image_projection.named_parameters():
                param.requires_grad = train_image_encoder
        for _, param in self.svg_transformer.transformer.named_parameters():
            param.requires_grad = train_LLM

    def use_image_encoder(self):
        return self.task == 'im2svg'

    def get_adapter(self, config, **kwargs):
        # Determine hidden size and query length based on the image encoder type.
        if config.image_encoder_type == 'clip':
            hidden_size = self.image_encoder.num_features
            self.query_length = 257
        elif config.image_encoder_type == 'vqgan':
            hidden_size = 256
            self.query_length = 196
        else:
            hidden_size = 256  # default fallback
            self.query_length = 200
        llm_hidden_size = config.hidden_size  # assuming the transformer hidden size
        return Adapter(hidden_size, llm_hidden_size, adapter_norm=config.adapter_norm, query_length=self.query_length, dropout_prob=kwargs.get('dropout', 0.1))

    def forward(self, batch):
        # Simplified forward pass where we assume batch has an "image" key.
        image = batch["image"]
        if self.use_image_encoder():
            embedded_image = self.image_encoder(image)
            conditioning_embeds = self.image_projection(embedded_image)
            # For demo purposes, we generate dummy input embeddings (replace with your logic)
            inputs_embeds = self.svg_transformer.transformer.wte(
                torch.randint(0, self.svg_transformer.transformer.wte.num_embeddings, (image.size(0), self.max_length))
            )
        else:
            inputs_embeds = self.svg_transformer.transformer.wte(
                torch.randint(0, self.svg_transformer.transformer.wte.num_embeddings, (image.size(0), self.max_length))
            )
        return inputs_embeds  # Dummy return

    def generate_im2svg(self, batch, **kwargs):
        # Prepare generation inputs (dummy implementation)
        image = batch["image"]
        if self.use_image_encoder():
            embedded_image = self.image_encoder(image)
            conditioning_embeds = self.image_projection(embedded_image)
        else:
            conditioning_embeds = torch.zeros((image.size(0), 10, 1), device=image.device)
        generation_output = self.svg_transformer.transformer.generate(inputs_embeds=conditioning_embeds, max_length=kwargs.get('max_length', 30))
        raw_svg = self.svg_transformer.tokenizer.batch_decode(generation_output, skip_special_tokens=True)
        return raw_svg

    @abstractmethod
    def _get_embeddings(self, input_ids):
        """Get embeddings from input ids - implementation differs between v1 and v2"""
        pass

    @abstractmethod
    def _get_svg_text(self, svg_list):
        """Get SVG text with appropriate end tokens - implementation differs between v1 and v2"""
        pass

# V1 implementation: Delegates transformer creation to the external LLM file.
class StarVectorStarCoder(StarVectorBase):
    def __init__(self, config, **kwargs):
        super().__init__(config, **kwargs)
    
    def _get_svg_transformer(self, config, **kwargs):
        from starvector.model.llm.starcoder import StarCoderModel  # V1: use StarCoderModel from external file
        return StarCoderModel(config, **kwargs)

    def _get_embeddings(self, input_ids):
        """V1-specific embedding method"""
        # This follows the implementation in starvector/model/models/starvector_v1.py.
        return self.svg_transformer.transformer.transformer.wte(input_ids)

    def _get_svg_text(self, svg_list):
        """V1-specific SVG text preparation"""
        return [t + self.svg_transformer.tokenizer.eos_token for t in svg_list]

# V2 implementation: Delegates transformer creation to the external V2 LLM file.
class StarVectorStarCoder2(StarVectorBase):
    def __init__(self, config, **kwargs):
        super().__init__(config, **kwargs)
    
    def _get_svg_transformer(self, config, **kwargs):
        from starvector.model.llm.starcoder2 import StarCoderModel  # V2: use external StarCoderModel from starcoder2.py
        return StarCoderModel(config, **kwargs)

    def _get_embeddings(self, input_ids):
        """V2-specific embedding method"""
        return self.svg_transformer.transformer.model.embed_tokens(input_ids)

    def _get_svg_text(self, svg_list):
        """V2-specific SVG text preparation"""
        return [t + self.svg_transformer.svg_end_token + self.svg_transformer.tokenizer.eos_token for t in svg_list]

    def _get_im2svg_specific_kwargs(self, kwargs):
        """V2-specific generation kwargs"""
        return {
            'eos_token_id': self.svg_transformer.svg_end_token_id,
        }

    def _get_text2svg_specific_kwargs(self, kwargs):
        """V2-specific text2svg generation kwargs"""
        return {
            'eos_token_id': self.svg_transformer.tokenizer.eos_token_id,
        }

# === Main Model Class for Hugging Face ===

class StarVectorForCausalLM(PreTrainedModel):
    config_class = StarVectorConfig
    _no_split_modules = []
    
    def __init__(self, config, **kwargs):
        super().__init__(config)
        # Choose V2 if the model name indicates starcoder2; otherwise use V1.
        if "starcoder2" in config.starcoder_model_name.lower():
            self.model = StarVectorStarCoder2(config=config, **kwargs)
        else:
            self.model = StarVectorStarCoder(config=config, **kwargs)

    def forward(self, batch):
        return self.model(batch)

    def generate_im2svg(self, batch, **kwargs):
        return self.model.generate_im2svg(batch, **kwargs)
    
    def generate_im2text(self, batch, **kwargs):
        return self.model.generate_im2text(batch, **kwargs)

    def process_images(self, images):
        return self.model.image_encoder.process_images(images)

# === Registration for Autonomous Loading ===

StarVectorConfig.register_for_auto_class()
StarVectorForCausalLM.register_for_auto_class("AutoModelForCausalLM") 
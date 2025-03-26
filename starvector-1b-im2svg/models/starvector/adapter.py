import torch.nn as nn

class Adapter(nn.Module):
    def __init__(self, in_features, out_features, adapter_norm="layer_norm", query_length=1, dropout_prob=0.1):
        super().__init__()
        self.fc = nn.Linear(in_features, out_features)
        self.norm = nn.LayerNorm(out_features) if adapter_norm == "layer_norm" else None
        self.dropout = nn.Dropout(dropout_prob)
        self.query_length = query_length

    def forward(self, x):
        out = self.fc(x)
        if self.norm is not None:
            out = self.norm(out)
        return self.dropout(out) 
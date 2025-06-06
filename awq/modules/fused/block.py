import os
import torch.nn as nn
from awq.modules.fused.attn import QuantAttentionFused


class MixtralBlock(nn.Module):
    def __init__(
        self,
        hidden_size,
        n_heads,
        n_kv_heads,
        qkv_layer,
        o_proj,
        moe,
        norm_1,
        norm_2,
        dev,
        max_seq_len,
        rope_theta,
    ):
        super().__init__()
        self.n_heads = n_heads
        self.n_kv_heads = n_kv_heads
        self.hidden_size = hidden_size
        self.norm_1 = norm_1.to(dev)
        self.attn = QuantAttentionFused(
            self.hidden_size,
            self.n_heads,
            self.n_kv_heads,
            qkv_layer,
            o_proj,
            dev=dev,
            max_seq_len=max_seq_len,
            use_alibi=False,
            rope_theta=rope_theta,
        ).to(dev)
        self.norm_2 = norm_2.to(dev)
        self.moe = moe
        self.device = dev

    def forward(
        self,
        hidden_states,
    ):
        norm_out = self.norm_1(hidden_states)
        attn_output, _, _ = self.attn.forward(
            hidden_states=norm_out,
        )

        h = hidden_states.to(attn_output.device) + attn_output
        out = self.moe.forward(self.norm_2(h))
        out = h + out

        return out


class LlamaLikeBlock(nn.Module):
    """
    LlamaLikeBlock is intended to be reused across blocks that have
    an architecture that closely resembles Llama, e.g. Mistral and Aquila.
    """

    def __init__(
        self,
        hidden_size,
        n_heads,
        n_kv_heads,
        qkv_layer,
        o_proj,
        mlp,
        norm_1,
        norm_2,
        dev,
        max_seq_len,
        rope_theta=10000,
        partial_rotary_factor=1.0,
        use_alibi=False,
        head_dim=None,
    ):
        super().__init__()
        self.n_heads = n_heads
        self.n_kv_heads = n_kv_heads
        self.head_dim = hidden_size // n_heads

        # To support gemma-7b, its head_dim is separate
        if head_dim:
            self.head_dim = head_dim

        self.hidden_size = hidden_size
        self.norm_1 = norm_1.to(dev)
        self.attn = QuantAttentionFused(
            self.hidden_size,
            self.n_heads,
            self.n_kv_heads,
            qkv_layer,
            o_proj,
            dev=dev,
            max_seq_len=max_seq_len,
            use_alibi=use_alibi,
            rope_theta=rope_theta,
            partial_rotary_factor=partial_rotary_factor,
            head_dim=head_dim,
        ).to(dev)
        self.norm_2 = norm_2.to(dev)
        self.mlp = mlp.to(dev)
        self.device = dev

    def forward(
        self,
        hidden_states,
    ):
        norm_out = self.norm_1(hidden_states)
        attn_output, _, _ = self.attn.forward(
            hidden_states=norm_out,
        )

        h = hidden_states.to(attn_output.device) + attn_output
        out = h + self.mlp.forward(self.norm_2(h))

        return out

class QwenBlock(nn.Module):
    """
    QwenBlock is intended to be reused across blocks that have
    an architecture that closely resembles Qwen2/Qwen3, e.g. use q_norm and k_norm.
    """

    def __init__(
        self,
        hidden_size,
        n_heads,
        n_kv_heads,
        qkv_layer,
        o_proj,
        mlp,
        norm_1,
        norm_2,        
        dev,
        max_seq_len,
        rope_theta=10000,
        partial_rotary_factor=1.0,
        use_alibi=False,
        head_dim=None,
        q_norm=None,
        k_norm=None,
    ):
        super().__init__()
        self.n_heads = n_heads
        self.n_kv_heads = n_kv_heads
        self.head_dim = hidden_size // n_heads

        # To support qwen3, its head_dim is separate
        if head_dim:
            self.head_dim = head_dim

        self.hidden_size = hidden_size
        self.norm_1 = norm_1.to(dev)
        self.attn = QuantAttentionFused(
            self.hidden_size,
            self.n_heads,
            self.n_kv_heads,
            qkv_layer,
            o_proj,
            dev=dev,
            max_seq_len=max_seq_len,
            use_alibi=use_alibi,
            rope_theta=rope_theta,
            partial_rotary_factor=partial_rotary_factor,
            head_dim=head_dim,
            q_norm=q_norm,
            k_norm=k_norm,
        ).to(dev)
        self.norm_2 = norm_2.to(dev)
        self.mlp = mlp.to(dev)
        self.device = dev

    def forward(
        self,
        hidden_states,
    ):
        norm_out = self.norm_1(hidden_states)
        attn_output, _, _ = self.attn.forward(
            hidden_states=norm_out,
        )

        h = hidden_states.to(attn_output.device) + attn_output
        out = h + self.mlp.forward(self.norm_2(h))

        return out

class Gemma2LikeBlock(nn.Module):
    def __init__(
        self,
        hidden_size,
        n_heads,
        n_kv_heads,
        qkv_layer,
        o_proj,
        mlp,
        norm_1,
        norm_2,
        norm_3,
        norm_4,
        dev,
        max_seq_len,
        rope_theta=10000,
        partial_rotary_factor=1.0,
        use_alibi=False,
        head_dim=None,
        attn_logit_softcapping=None,
    ):
        super().__init__()
        self.n_heads = n_heads
        self.n_kv_heads = n_kv_heads
        self.head_dim = hidden_size // n_heads

        if head_dim:
            self.head_dim = head_dim

        self.hidden_size = hidden_size
        self.norm_1 = norm_1.to(dev)
        self.attn = QuantAttentionFused(
            self.hidden_size,
            self.n_heads,
            self.n_kv_heads,
            qkv_layer,
            o_proj,
            dev=dev,
            max_seq_len=max_seq_len,
            use_alibi=use_alibi,
            rope_theta=rope_theta,
            partial_rotary_factor=partial_rotary_factor,
            head_dim=head_dim,
            attn_logit_softcapping=attn_logit_softcapping,
        ).to(dev)

        self.norm_2 = norm_2.to(dev)
        self.norm_3 = norm_3.to(dev)
        self.mlp = mlp.to(dev)
        self.norm_4 = norm_4.to(dev)
        self.device = dev

    def forward(
        self,
        hidden_states,
    ):
        residual = hidden_states
        hidden_states = self.norm_1(hidden_states)

        hidden_states, _, _ = self.attn.forward(
            hidden_states=hidden_states,
        )

        hidden_states = self.norm_2(hidden_states)
        hidden_states = residual + hidden_states

        residual = hidden_states
        hidden_states = self.norm_3(hidden_states)
        hidden_states = self.mlp(hidden_states)
        hidden_states = self.norm_4(hidden_states)
        out = residual + hidden_states

        return out


class CohereBlock(nn.Module):
    def __init__(
        self,
        hidden_size,
        n_heads,
        n_kv_heads,
        qkv_layer,
        o_proj,
        mlp,
        norm_1,
        dev,
        max_seq_len,
        rope_theta=10000,
        partial_rotary_factor=1.0,
        use_alibi=False,
        head_dim=None,
    ):
        super().__init__()
        self.n_heads = n_heads
        self.n_kv_heads = n_kv_heads
        self.head_dim = hidden_size // n_heads

        # To support gemma-7b, its head_dim is separate
        if head_dim:
            self.head_dim = head_dim
        self.hidden_size = hidden_size
        self.norm_1 = norm_1.to(dev)
        self.attn = QuantAttentionFused(
            self.hidden_size,
            self.n_heads,
            self.n_kv_heads,
            qkv_layer,
            o_proj,
            dev=dev,
            max_seq_len=max_seq_len,
            use_alibi=use_alibi,
            rope_theta=rope_theta,
            partial_rotary_factor=partial_rotary_factor,
            head_dim=head_dim,
            is_neox=False,
        ).to(dev)
        self.mlp = mlp.to(dev)
        self.device = dev

    def forward(
        self,
        hidden_states,
    ):
        norm_out = self.norm_1(hidden_states)
        attn_output, _, _ = self.attn.forward(
            hidden_states=norm_out,
        )

        h = hidden_states.to(attn_output.device) + attn_output
        out = h + self.mlp.forward(norm_out)

        return out


class MPTBlock(nn.Module):
    def __init__(
        self,
        hidden_size,
        n_heads,
        qkv_layer,
        o_proj,
        mpt_mlp,
        norm_1,
        norm_2,
        dev,
        max_seq_len,
    ):
        super().__init__()
        self.n_heads = n_heads
        self.n_kv_heads = 0
        self.hidden_size = hidden_size
        self.norm_1 = norm_1
        self.attn = QuantAttentionFused(
            hidden_size,
            self.n_heads,
            self.n_kv_heads,
            qkv_layer,
            o_proj,
            dev=dev,
            max_seq_len=max_seq_len,
            use_alibi=True,
        ).to(dev)
        self.norm_2 = norm_2
        self.ffn = mpt_mlp.to(dev)
        self.device = dev

    def forward(
        self,
        hidden_states,
    ):
        norm_out = self.norm_1(hidden_states)
        attn_output, _, _ = self.attn.forward(
            hidden_states=norm_out,
        )

        h = hidden_states.to(attn_output.device) + attn_output
        out = h + self.ffn.forward(self.norm_2(h))
        return out


class FalconDecoderLayer(nn.Module):
    def __init__(
        self,
        hidden_size,
        n_heads,
        qkv_layer,
        o_proj,
        mlp,
        dev,
        max_seq_len,
        input_layernorm=None,
        ln_attn=None,
        ln_mlp=None,
        new_decoder_arch=True,
    ):
        super().__init__()
        self.n_heads = n_heads
        self.n_kv_heads = 8 if new_decoder_arch else 0
        self.hidden_size = hidden_size
        self.new_decoder_arch = new_decoder_arch

        if new_decoder_arch:
            attention_shapes = None
        else:
            attention_shapes = self._get_attention_shapes(
                n_heads, max_seq_len, self.hidden_size // n_heads
            )

        # TODO: Falcon has ALiBi implemented but which model uses it?
        self.attn = QuantAttentionFused(
            hidden_size,
            self.n_heads,
            self.n_kv_heads,
            qkv_layer,
            o_proj,
            dev=dev,
            max_seq_len=max_seq_len,
            use_alibi=False,
            attention_shapes=attention_shapes,
        ).to(dev)

        if new_decoder_arch:
            self.ln_attn = ln_attn  # before attention
            self.ln_mlp = ln_mlp  # before mlp
        else:
            self.input_layernorm = input_layernorm  # before attention

        self.mlp = mlp
        self.device = dev

    def _get_attention_shapes(self, n_heads, max_seq_len, head_dim):
        batch_size = int(os.getenv("AWQ_BATCH_SIZE", "1"))

        self.attention_shapes = {
            # following fastertransformer definition
            "cache_v": (
                batch_size,
                1,
                max_seq_len,
                head_dim,
            ),
            # 8: pack 8 fp16 in FT, if fp32 then use 4
            "cache_k": (
                batch_size,
                1,
                head_dim // 8,
                max_seq_len,
                8,
            ),
            "xqkv_view": (n_heads + 2, head_dim),
            "xq_slice": lambda xqkv: xqkv[:, :, :-2],
            "xk_slice": lambda xqkv: xqkv[:, :, [-2]],
            "xv_slice": lambda xqkv: xqkv[:, :, [-1]],
            "xq_view": (n_heads, head_dim),
            "xk_view": (1, head_dim),
            "xv_view": (1, head_dim),
            "xk_reshape": (1, head_dim // 8, 8),
            "single_xq_view": (n_heads, head_dim),
            "single_xk_view": (1, head_dim),
            "single_xv_view": (1, head_dim),
        }

        return self.attention_shapes

    def forward(
        self,
        hidden_states,
    ):
        if self.new_decoder_arch:
            layernorm_out = self.ln_attn(hidden_states)
            mlp_layernorm_out = self.ln_mlp(hidden_states)
        else:
            layernorm_out = self.input_layernorm(hidden_states)

        attn_output, _, _ = self.attn.forward(
            hidden_states=layernorm_out,
        )

        h_attn = hidden_states.to(attn_output.device) + attn_output

        if self.new_decoder_arch:
            h_mlp = self.mlp.forward(mlp_layernorm_out)
        else:
            h_mlp = self.mlp.forward(layernorm_out)

        out = h_attn + h_mlp

        return out


class Phi3Block(nn.Module):
    """
    Phi3Block is intended to be reused across blocks that have
    an architecture that closely resembles Phi-3.
    """

    def __init__(
        self,
        hidden_size,
        n_heads,
        n_kv_heads,
        qkv_layer,
        o_proj,
        mlp,
        norm_1,
        norm_2,
        dev,
        max_seq_len,
        rope_theta=10000,
        rope_scaling=None,
        use_alibi=False,
        head_dim=None,
    ):
        super().__init__()
        self.n_heads = n_heads
        self.n_kv_heads = n_kv_heads
        self.head_dim = hidden_size // n_heads

        # To support models with separate head_dim
        if head_dim:
            self.head_dim = head_dim

        self.hidden_size = hidden_size
        self.norm_1 = norm_1.to(dev)
        self.attn = QuantAttentionFused(
            self.hidden_size,
            self.n_heads,
            self.n_kv_heads,
            qkv_layer,
            o_proj,
            dev=dev,
            max_seq_len=max_seq_len,
            use_alibi=use_alibi,
            rope_theta=rope_theta,
            rope_scaling=rope_scaling,
            head_dim=head_dim,
        ).to(dev)
        self.norm_2 = norm_2.to(dev)
        self.mlp = mlp.to(dev)
        self.device = dev

    def forward(
        self,
        hidden_states,
    ):
        norm_out = self.norm_1(hidden_states)
        attn_output, _, _ = self.attn.forward(
            hidden_states=norm_out,
        )

        h = hidden_states.to(attn_output.device) + attn_output
        out = h + self.mlp.forward(self.norm_2(h))

        return out

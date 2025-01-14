{% from './macros/includes.md' import render_fields, render_yaml %}
{% set mv_details = "See [Missing Value Strategy](./input_features.md#missing-value-strategy) for details." %}
{% set details = {"missing_value_strategy": mv_details} %}

# Preprocessing

Text features are an extension of [sequence features](../sequence_features). Text inputs are processed by a tokenizer
which maps the raw text input into a sequence of tokens. An integer id is assigned to each unique token. Using this
mapping, each text string is converted first to a sequence of tokens, and next to a sequence of integers.

The list of tokens and their integer representations (vocabulary) is stored in the metadata of the model. In the case of
a text output feature, this same mapping is used to post-process predictions to text.

{% set text_preprocessing = get_feature_preprocessing_schema("text") %}
{{ render_yaml(text_preprocessing, parent="preprocessing") }}

Parameters:

{{ render_fields(schema_class_to_fields(text_preprocessing), details=details) }}

Preprocessing parameters can also be defined once and applied to all text input features using the [Type-Global Preprocessing](../defaults.md#type-global-preprocessing) section.

!!! note
    If a text feature's encoder specifies a huggingface model, then the tokenizer for that model will be used
    automatically.

# Input Features

The encoder parameters specified at the feature level are:

- **`tied`** (default `null`): name of another input feature to tie the weights of the encoder with. It needs to be the name of
a feature of the same type and with the same encoder parameters.

Example text feature entry in the input features list:

```yaml
name: text_column_name
type: text
tied: null
encoder: 
    type: bert
    trainable: true
```

Parameters:

- **`type`** (default `parallel_cnn`): encoder to use for the input text feature. The available encoders include encoders
used for [Sequence Features](../sequence_features#sequence-input-features-and-encoders) as well as pre-trained text
encoders from the
face transformers library: `albert`, `auto_transformer`, `bert`, `camembert`, `ctrl`,
`distilbert`, `electra`, `flaubert`, `gpt`, `gpt2`, `longformer`, `roberta`, `t5`, `mt5`, `transformer_xl`, `xlm`,
`xlmroberta`, `xlnet`.

Encoder type and encoder parameters can also be defined once and applied to all text input features using
the [Type-Global Encoder](../defaults.md#type-global-encoder) section.

## Encoders

### Embed Encoder

``` mermaid
graph LR
  A["12\n7\n43\n65\n23\n4\n1"] --> B["emb_12\nemb__7\nemb_43\nemb_65\nemb_23\nemb__4\nemb__1"];
  B --> C["Aggregation\n Reduce\n Operation"];
  C --> ...;
```
{ data-search-exclude }

The embed encoder simply maps each token in the input sequence to an embedding, creating a `b x s x h` tensor where `b`
is the batch size, `s` is the length of the sequence and `h` is the embedding size.
The tensor is reduced along the `s` dimension to obtain a single vector of size `h` for each element of the batch.
If you want to output the full `b x s x h` tensor, you can specify `reduce_output: null`.

{% set text_encoder = get_encoder_schema("text", "embed") %}
{{ render_yaml(text_encoder, parent="encoder") }}

Parameters:

{{ render_fields(schema_class_to_fields(text_encoder, exclude=["type"])) }}

### Parallel CNN Encoder

``` mermaid
graph LR
  A["12\n7\n43\n65\n23\n4\n1"] --> C["emb_12\nemb__7\nemb_43\nemb_65\nemb_23\nemb__4\nemb__1"];
  C --> D1["1D Conv\n Width 2"] --> E1["Pool"];
  C --> D2["1D Conv\n Width 3"] --> E2["Pool"];
  C --> D3["1D Conv\n Width 4"] --> E3["Pool"];
  C --> D4["1D Conv\n Width 5"] --> E4["Pool"];
  E1 --> F["Concat"] --> G["Fully\n Connected\n Layers"] --> H["..."];
  E2 --> F;
  E3 --> F;
  E4 --> F;
```
{ data-search-exclude }

The parallel cnn encoder is inspired by
[Yoon Kim's Convolutional Neural Network for Sentence Classification](https://arxiv.org/abs/1408.5882).
It works by first mapping the input token sequence `b x s` (where `b` is the batch size and `s` is the length of the
sequence) into a sequence of embeddings, then it passes the embedding through a number of parallel 1d convolutional
layers with different filter size (by default 4 layers with filter size 2, 3, 4 and 5), followed by max pooling and
concatenation.
This single vector concatenating the outputs of the parallel convolutional layers is then passed through a stack of
fully connected layers and returned as a `b x h` tensor where `h` is the output size of the last fully connected layer.
If you want to output the full `b x s x h` tensor, you can specify `reduce_output: null`.

{% set text_encoder = get_encoder_schema("text", "parallel_cnn") %}
{{ render_yaml(text_encoder, parent="encoder") }}

Parameters:

{{ render_fields(schema_class_to_fields(text_encoder, exclude=["type"])) }}

### Stacked CNN Encoder

``` mermaid
graph LR
  A["12\n7\n43\n65\n23\n4\n1"] --> B["emb_12\nemb__7\nemb_43\nemb_65\nemb_23\nemb__4\nemb__1"];
  B --> C["1D Conv Layers\n Different Widths"];
  C --> D["Fully\n Connected\n Layers"];
  D --> ...;
```
{ data-search-exclude }

The stacked cnn encoder is inspired by [Xiang Zhang at all's Character-level Convolutional Networks for Text Classification](https://arxiv.org/abs/1509.01626).
It works by first mapping the input token sequence `b x s` (where `b` is the batch size and `s` is the length of the
sequence) into a sequence of embeddings, then it passes the embedding through a stack of 1d convolutional layers with
different filter size (by default 6 layers with filter size 7, 7, 3, 3, 3 and 3), followed by an optional final pool and
by a flatten operation.
This single flatten vector is then passed through a stack of fully connected layers and returned as a `b x h` tensor
where `h` is the output size of the last fully connected layer.
If you want to output the full `b x s x h` tensor, you can specify the `pool_size` of all your `conv_layers` to be
`null`  and `reduce_output: null`, while if `pool_size` has a value different from `null` and `reduce_output: null` the
returned tensor will be of shape `b x s' x h`, where `s'` is width of the output of the last convolutional layer.

{% set text_encoder = get_encoder_schema("text", "stacked_cnn") %}
{{ render_yaml(text_encoder, parent="encoder") }}

Parameters:

{{ render_fields(schema_class_to_fields(text_encoder, exclude=["type"])) }}

### Stacked Parallel CNN Encoder

``` mermaid
graph LR
  A["12\n7\n43\n65\n23\n4\n1"] --> C["emb_12\nemb__7\nemb_43\nemb_65\nemb_23\nemb__4\nemb__1"];
  C --> D1["1D Conv\n Width 2"] --> E["Concat"];
  C --> D2["1D Conv\n Width 3"] --> E;
  C --> D3["1D Conv\n Width 4"] --> E;
  C --> D4["1D Conv\n Width 5"] --> E;
  E --> F["..."];
  F --> G1["1D Conv\n Width 2"] --> H["Concat"];
  F --> G2["1D Conv\n Width 3"] --> H;
  F --> G3["1D Conv\n Width 4"] --> H;
  F --> G4["1D Conv\n Width 5"] --> H;
  H --> I["Pool"] --> J["Fully\n Connected\n Layers"] --> K["..."];
```
{ data-search-exclude }

The stacked parallel cnn encoder is a combination of the Parallel CNN and the Stacked CNN encoders where each layer of
the stack is composed of parallel convolutional layers.
It works by first mapping the input token sequence `b x s` (where `b` is the batch size and `s` is the length of the
sequence) into a sequence of embeddings, then it passes the embedding through a stack of several parallel 1d
convolutional layers with different filter size, followed by an optional final pool and by a flatten operation.
This single flattened vector is then passed through a stack of fully connected layers and returned as a `b x h` tensor
where `h` is the output size of the last fully connected layer.
If you want to output the full `b x s x h` tensor, you can specify `reduce_output: null`.

{% set text_encoder = get_encoder_schema("text", "stacked_parallel_cnn") %}
{{ render_yaml(text_encoder, parent="encoder") }}

Parameters:

{{ render_fields(schema_class_to_fields(text_encoder, exclude=["type"])) }}

### RNN Encoder

``` mermaid
graph LR
  A["12\n7\n43\n65\n23\n4\n1"] --> B["emb_12\nemb__7\nemb_43\nemb_65\nemb_23\nemb__4\nemb__1"];
  B --> C["RNN Layers"];
  C --> D["Fully\n Connected\n Layers"];
  D --> ...;
```
{ data-search-exclude }

The rnn encoder works by first mapping the input token sequence `b x s` (where `b` is the batch size and `s` is the
length of the sequence) into a sequence of embeddings, then it passes the embedding through a stack of recurrent layers
(by default 1 layer), followed by a reduce operation that by default only returns the last output, but can perform other
reduce functions.
If you want to output the full `b x s x h` where `h` is the size of the output of the last rnn layer, you can specify
`reduce_output: null`.

{% set text_encoder = get_encoder_schema("text", "rnn") %}
{{ render_yaml(text_encoder, parent="encoder") }}

Parameters:

{{ render_fields(schema_class_to_fields(text_encoder, exclude=["type"])) }}

### CNN RNN Encoder

``` mermaid
graph LR
  A["12\n7\n43\n65\n23\n4\n1"] --> B["emb_12\nemb__7\nemb_43\nemb_65\nemb_23\nemb__4\nemb__1"];
  B --> C1["CNN Layers"];
  C1 --> C2["RNN Layers"];
  C2 --> D["Fully\n Connected\n Layers"];
  D --> ...;
```
{ data-search-exclude }

The `cnnrnn` encoder works by first mapping the input token sequence `b x s` (where `b` is the batch size and `s` is
the length of the sequence) into a sequence of embeddings, then it passes the embedding through a stack of convolutional
layers (by default 2), that is followed by a stack of recurrent layers (by default 1), followed by a reduce operation
that by default only returns the last output, but can perform other reduce functions.
If you want to output the full `b x s x h` where `h` is the size of the output of the last rnn layer, you can specify
`reduce_output: null`.

{% set text_encoder = get_encoder_schema("text", "cnnrnn") %}
{{ render_yaml(text_encoder, parent="encoder") }}

Parameters:

{{ render_fields(schema_class_to_fields(text_encoder, exclude=["type"])) }}

### Transformer Encoder

``` mermaid
graph LR
  A["12\n7\n43\n65\n23\n4\n1"] --> B["emb_12\nemb__7\nemb_43\nemb_65\nemb_23\nemb__4\nemb__1"];
  B --> C["Transformer\n Blocks"];
  C --> D["Fully\n Connected\n Layers"];
  D --> ...;
```
{ data-search-exclude }

The `transformer` encoder implements a stack of transformer blocks, replicating the architecture introduced in the
[Attention is all you need](https://arxiv.org/abs/1706.03762) paper, and adds am optional stack of fully connected
layers at the end.

{% set text_encoder = get_encoder_schema("text", "transformer") %}
{{ render_yaml(text_encoder, parent="encoder") }}

Parameters:

{{ render_fields(schema_class_to_fields(text_encoder, exclude=["type"])) }}

### Huggingface encoders

All huggingface-based text encoders are configured with the following parameters:

- `pretrained_model_name_or_path` (default is the huggingface default model path for the specified encoder, i.e. `bert-base-uncased` for BERT). This can be either the name of a model or a path where it was downloaded. For details on the variants available refer to the [Hugging Face documentation](https://huggingface.co/docs/transformers/index#supported-models).
- `reduce_output` (default `cls_pooled`): defines how to reduce the output tensor along the `s` sequence length dimension if the rank of the tensor is greater than 2. Available values are: `cls_pooled`, `sum`, `mean` or `avg`, `max`, `concat` (concatenates along the first dimension), `last` (returns the last vector of the first dimension) and  `null` (which does not reduce and returns the full tensor).
- `trainable` (default `false`): if `true` the weights of the encoder will be trained, otherwise they will be kept frozen.

!!! note
    Any hyperparameter of any huggingface encoder can be overridden. Check the
    [huggingface documentation](https://huggingface.co/docs/transformers/index#supported-models) for which parameters are used for which models.

    ```yaml
    name: text_column_name
    type: text
    encoder: bert
    trainable: true
    num_attention_heads: 16 # Instead of 12
    ```

{% set hf_classes = get_hf_text_encoder_schemas() %}
{% for hf_encoder in hf_classes %}

#### {{ hf_encoder.module_name() }}

{{ schema_class_long_description(hf_encoder) }}

{{ render_yaml(hf_encoder, parent="encoder", updates={"pretrained_model_name_or_path": "bert"}) }}

Parameters:

{{ render_fields(schema_class_to_fields(hf_encoder, exclude=["type"])) }}
{% endfor %}

# Output Features

Text output features are a special case of [Sequence Features](#sequence-output-features-and-decoders), so all options
of sequence features are available for text features as well.

Text output features can be used for either tagging (classifying each token of an input sequence) or text
generation (generating text by repeatedly sampling from the model). There are two decoders available for these tasks
named `tagger` and `generator` respectively.

Example text output feature using default parameters:

```yaml
name: text_column_name
type: text
reduce_input: null
dependencies: []
reduce_dependencies: sum
loss:
    type: softmax_cross_entropy
    confidence_penalty: 0
    robust_lambda: 0
    class_weights: 1
    class_similarities_temperature: 0
decoder: 
    type: generator
```

Parameters:

- **`reduce_input`** (default `sum`): defines how to reduce an input that is not a vector, but a matrix or a higher order
tensor, on the first dimension (second if you count the batch dimension). Available values are: `sum`, `mean` or `avg`,
`max`, `concat` (concatenates along the sequence dimension), `last` (returns the last vector of the sequence dimension).
- **`dependencies`** (default `[]`): the output features this one is dependent on. For a detailed explanation refer to
[Output Feature Dependencies](../output_features#output-feature-dependencies).
- **`reduce_dependencies`** (default `sum`): defines how to reduce the output of a dependent feature that is not a vector,
but a matrix or a higher order tensor, on the first dimension (second if you count the batch dimension). Available
values are: `sum`, `mean` or `avg`, `max`, `concat` (concatenates along the sequence dimension), `last` (returns the
last vector of the sequence dimension).
- **`loss`** (default `{type: softmax_cross_entropy, class_similarities_temperature: 0, class_weights: 1,
confidence_penalty: 0, robust_lambda: 0}`): is a dictionary containing a loss `type`. The only available loss `type` for
text features is `softmax_cross_entropy`. See [Loss](#loss) for details.
- **`decoder`** (default: `{"type": "generator"}`): Decoder for the desired task. Options: `generator`, `tagger`. See [Decoder](#decoder) for details.

Decoder type and decoder parameters can also be defined once and applied to all text output features using
the [Type-Global Decoder](../defaults.md#type-global-decoder) section. Loss and loss related parameters can
also be defined once in the same way.

## Decoders

### Generator

``` mermaid
graph LR
  A["Combiner Output"] --> B["Fully\n Connected\n Layers"];
  B --> C1["RNN"] --> C2["RNN"] --> C3["RNN"];
  GO(["GO"]) -.-o C1;
  C1 -.-o O1("Output");
  O1 -.-o C2;
  C2 -.-o O2("Output");
  O2 -.-o C3;
  C3 -.-o END(["END"]);
  subgraph DEC["DECODER.."]
  B
  C1
  C2
  C3
  end
```
{ data-search-exclude }

In the case of `generator` the decoder is a (potentially empty) stack of fully connected layers, followed by an RNN that
generates outputs feeding on its own previous predictions and generates a tensor of size `b x s' x c`, where `b` is the
batch size, `s'` is the length of the generated sequence and `c` is the number of classes, followed by a
softmax_cross_entropy.
During training teacher forcing is adopted, meaning the list of targets is provided as both inputs and outputs (shifted
by 1), while at evaluation time greedy decoding (generating one token at a time and feeding it as input for the next
step) is performed by beam search, using a beam of 1 by default.
In general a generator expects a `b x h` shaped input tensor, where `h` is a hidden dimension.
The `h` vectors are (after an optional stack of fully connected layers) fed into the rnn generator.
One exception is when the generator uses attention, as in that case the expected size of the input tensor is
`b x s x h`, which is the output of a sequence, text or time series input feature without reduced outputs or the output
of a sequence-based combiner.
If a `b x h` input is provided to a generator decoder using an RNN with attention instead, an error will be raised
during model building.

{% set decoder = get_decoder_schema("text", "generator") %}
{{ render_yaml(decoder, parent="decoder") }}

Parameters:

{{ render_fields(schema_class_to_fields(decoder, exclude=["type"])) }}

### Tagger

``` mermaid
graph LR
  A["emb[0]\n....\nemb[n]"] --> B["Fully\n Connected\n Layers"];
  B --> C["Projection\n....\nProjection"];
  C --> D["Softmax\n....\nSoftmax"];
  subgraph DEC["DECODER.."]
  B
  C
  D
  end
  subgraph COM["COMBINER OUT.."]
  A
  end
```
{ data-search-exclude }

In the case of `tagger` the decoder is a (potentially empty) stack of fully connected layers, followed by a projection
into a tensor of size `b x s x c`, where `b` is the batch size, `s` is the length of the sequence and `c` is the number
of classes, followed by a softmax_cross_entropy.
This decoder requires its input to be shaped as `b x s x h`, where `h` is a hidden dimension, which is the output of a
sequence, text or time series input feature without reduced outputs or the output of a sequence-based combiner.
If a `b x h` input is provided instead, an error will be raised during model building.

{% set decoder = get_decoder_schema("text", "tagger") %}
{{ render_yaml(decoder, parent="decoder") }}

Parameters:

{{ render_fields(schema_class_to_fields(decoder, exclude=["type"])) }}

## Loss

### Sequence Softmax Cross Entropy

{% set loss = get_loss_schema("sequence_softmax_cross_entropy") %}
{{ render_yaml(loss, parent="loss") }}

Parameters:

{{ render_fields(schema_class_to_fields(loss, exclude=["type"])) }}

## Metrics

The metrics available for text features are the same as for [Sequence Features](../sequence_features#sequence-features-metrics):

- `sequence_accuracy` The rate at which the model predicted the correct sequence.
- `token_accuracy` The number of tokens correctly predicted divided by the total number of tokens in all sequences.
- `last_accuracy` Accuracy considering only the last element of the sequence. Useful to ensure special end-of-sequence
tokens are generated or tagged.
- `edit_distance` Levenshtein distance: the minimum number of single-token edits (insertions, deletions or substitutions)
required to change predicted sequence to ground truth.
- `perplexity` Perplexity is the inverse of the predicted probability of the ground truth sequence, normalized by the
number of tokens. The lower the perplexity, the higher the probability of predicting the true sequence.
- `loss` The value of the loss function.

You can set any of the above as `validation_metric` in the `training` section of the configuration if `validation_field`
names a sequence feature.

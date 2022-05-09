# Postprocessing operations in model spec 0.4
The supported operations that are valid in postprocessing. IMPORTANT: these operations must return float32 tensors, so that their output can be consumed by the models.
### `binarize`
Binarize the tensor with a fixed threshold, values above the threshold will be set to one, values below the threshold to zero.
- key word arguments:
  - `threshold` The fixed threshold
- reference implementation: https://github.com/bioimage-io/core-bioimage-io-python/blob/main/bioimageio/core/prediction_pipeline/_processing.py#L104-L109
### `clip`
Set tensor values below min to min and above max to max.
- key word arguments:
  - `max` maximum value for clipping
  - `min` minimum value for clipping
- reference implementation: https://github.com/bioimage-io/core-bioimage-io-python/blob/main/bioimageio/core/prediction_pipeline/_processing.py#L112-L118
### `scale_linear`
Fixed linear scaling.
- key word arguments:
  - `axes` The subset of axes to scale jointly. For example xy to scale the two image axes for 2d data jointly. The batch axis (b) is not valid here.
  - `[gain]` multiplicative factor
  - `[offset]` additive term
- reference implementation: https://github.com/bioimage-io/core-bioimage-io-python/blob/main/bioimageio/core/prediction_pipeline/_processing.py#L129-L152
### `scale_mean_variance`
Scale the tensor s.t. its mean and variance match a reference tensor.
- key word arguments:
  - `mode` One of per_dataset (mean and variance are computed for the entire dataset), per_sample (mean and variance are computed for each sample individually)
  - `reference_tensor` Name of tensor to match.
- reference implementation: https://github.com/bioimage-io/core-bioimage-io-python/blob/main/bioimageio/core/prediction_pipeline/_processing.py#L155-L157
### `scale_range`
Scale with percentiles.
- key word arguments:
  - `axes` The subset of axes to normalize jointly. For example xy to normalize the two image axes for 2d data jointly. The batch axis (b) is not valid here.
  - `mode` One of per_dataset (mean and variance are computed for the entire dataset), per_sample (mean and variance are computed for each sample individually)
  - `[eps]` Epsilon for numeric stability: `out = (tensor - v_lower) / (v_upper - v_lower + eps)`; with `v_lower,v_upper` values at the respective percentiles. Default value: 10^-6.
  - `[max_percentile]` The upper percentile used for normalization, in range 1 to 100. Has to be bigger than min_percentile. Default value: 100. The range is 1 to 100 instead of 0 to 100 to avoid mistakenly accepting percentiles specified in the range 0.0 to 1.0.
  - `[min_percentile]` The lower percentile used for normalization, in range 0 to 100. Default value: 0.
  - `[reference_tensor]` Tensor name to compute the percentiles from. Default: The tensor itself. If mode==per_dataset this needs to be the name of an input tensor.
- reference implementation: https://github.com/bioimage-io/core-bioimage-io-python/blob/main/bioimageio/core/prediction_pipeline/_processing.py#L160-L184
### `sigmoid`

- reference implementation: https://github.com/bioimage-io/core-bioimage-io-python/blob/main/bioimageio/core/prediction_pipeline/_processing.py#L187-L190
### `zero_mean_unit_variance`
Subtract mean and divide by variance.
- key word arguments:
  - `axes` The subset of axes to normalize jointly. For example xy to normalize the two image axes for 2d data jointly. The batch axis (b) is not valid here.
  - `mode` One of fixed (fixed values for mean and variance), per_dataset (mean and variance are computed for the entire dataset), per_sample (mean and variance are computed for each sample individually)
  - `[eps]` epsilon for numeric stability: `out = (tensor - mean) / (std + eps)`. Default value: 10^-6.
  - `[mean]` The mean value(s) to use for `mode == fixed`. For example `[1.1, 2.2, 3.3]` in the case of a 3 channel image where the channels are not normalized jointly.
  - `[std]` The standard deviation values to use for `mode == fixed`. Analogous to mean.
- reference implementation: https://github.com/bioimage-io/core-bioimage-io-python/blob/main/bioimageio/core/prediction_pipeline/_processing.py#L193-L222
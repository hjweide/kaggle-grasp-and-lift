import theano.tensor as T
import subsample
from lasagne import layers
from lasagne import nonlinearities
from lasagne import init
#from lasagne.layers import cuda_convnet
from lasagne.layers import conv
from lasagne.layers import pool

#Conv1DLayer = cuda_convnet.Conv1DCCLayer
#MaxPool1DLayer = cuda_convnet.MaxPool1DCCLayer

Conv1DLayer = conv.Conv1DLayer
MaxPool1DLayer = pool.MaxPool1DLayer
SubsampleLayer = subsample.SubsampleLayer


class WindowNormLayer(layers.Layer):
    def __init__(self, incoming, **kwargs):
        super(WindowNormLayer, self).__init__(incoming, **kwargs)

    def get_output_for(self, input, **kwargs):
        X_min = T.min(input, axis=2).reshape((-1, input.shape[1], 1))
        X_max = T.max(input, axis=2).reshape((-1, input.shape[1], 1))

        return (input - X_min) / (X_max - X_min)


def build_model(batch_size,
                num_channels,
                input_length,
                output_dim,):
    l_in = layers.InputLayer(
        shape=(batch_size, num_channels, input_length),
        name='input',
    )

    # window size should be 1600 for this network
    l_ss_left = SubsampleLayer(
        l_in,
        window=(None, 1000, 10),
        name='l_ss_left',
    )

    l_ss_right = SubsampleLayer(
        l_in,
        window=(1000, None, 10),
        name='l_ss_right',
    )

    l_window_left = WindowNormLayer(
        l_ss_left,
        name='l_window_left',
    )

    l_window_right = WindowNormLayer(
        l_ss_right,
        name='l_window_right',
    )

    l_conv1_left = Conv1DLayer(
        l_window_left,
        name='conv1_left',
        num_filters=8,
        border_mode='valid',
        filter_size=3,
        nonlinearity=nonlinearities.rectify,
        W=init.Orthogonal(),
    )

    l_conv1_right = Conv1DLayer(
        l_window_right,
        name='conv1_right',
        num_filters=8,
        border_mode='valid',
        filter_size=3,
        nonlinearity=nonlinearities.rectify,
        W=init.Orthogonal(),
    )

    l_pool1_left = MaxPool1DLayer(
        l_conv1_left,
        name='pool1_left',
        pool_size=3,
        stride=2,
    )

    l_pool1_right = MaxPool1DLayer(
        l_conv1_right,
        name='pool1_right',
        pool_size=3,
        stride=2,
    )

    l_dropout_conv2_left = layers.DropoutLayer(
        l_pool1_left,
        name='drop_conv2_left',
        p=0.1,
    )

    l_dropout_conv2_right = layers.DropoutLayer(
        l_pool1_right,
        name='drop_conv2_right',
        p=0.1,
    )

    l_conv2_left = Conv1DLayer(
        l_dropout_conv2_left,
        name='conv2_left',
        num_filters=16,
        border_mode='valid',
        filter_size=3,
        nonlinearity=nonlinearities.rectify,
        W=init.Orthogonal(),
    )

    l_conv2_right = Conv1DLayer(
        l_dropout_conv2_right,
        name='conv2_right',
        num_filters=16,
        border_mode='valid',
        filter_size=3,
        nonlinearity=nonlinearities.rectify,
        W=init.Orthogonal(),
    )

    l_dropout_conv3_left = layers.DropoutLayer(
        l_conv2_left,
        name='drop_conv3_left',
        p=0.2,
    )

    l_dropout_conv3_right = layers.DropoutLayer(
        l_conv2_right,
        name='drop_conv3_right',
        p=0.2,
    )

    l_conv3_left = Conv1DLayer(
        l_dropout_conv3_left,
        name='conv3_left',
        num_filters=32,
        border_mode='valid',
        filter_size=3,
        nonlinearity=nonlinearities.rectify,
        W=init.Orthogonal(),
    )

    l_conv3_right = Conv1DLayer(
        l_dropout_conv3_right,
        name='conv3_right',
        num_filters=32,
        border_mode='valid',
        filter_size=3,
        nonlinearity=nonlinearities.rectify,
        W=init.Orthogonal(),
    )

    l_pool3_left = MaxPool1DLayer(
        l_conv3_left,
        name='pool3_left',
        pool_size=3,
        stride=2,
    )

    l_pool3_right = MaxPool1DLayer(
        l_conv3_right,
        name='pool3_right',
        pool_size=3,
        stride=2,
    )

    l_concat = layers.ConcatLayer(
        incomings=(l_pool3_left, l_pool3_right),
        name='concat',
    )

    l_dropout_dense1 = layers.DropoutLayer(
        l_concat,
        name='drop_dense1',
        p=0.5,
    )

    l_dense1 = layers.DenseLayer(
        l_dropout_dense1,
        name='dense1',
        num_units=128,
        nonlinearity=nonlinearities.rectify,
        W=init.Orthogonal(),
    )

    l_dropout_dense2 = layers.DropoutLayer(
        l_dense1,
        name='drop_dense2',
        p=0.5,
    )

    l_dense2 = layers.DenseLayer(
        l_dropout_dense2,
        name='dense2',
        num_units=128,
        nonlinearity=nonlinearities.rectify,
        W=init.Orthogonal(),
    )

    l_out = layers.DenseLayer(
        l_dense2,
        name='output',
        num_units=output_dim,
        nonlinearity=nonlinearities.sigmoid,
        W=init.Orthogonal(),
    )

    return l_out

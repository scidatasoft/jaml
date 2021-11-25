from keras.callbacks import Callback
from keras.layers import Dense, Dropout, Activation
from keras.layers.advanced_activations import LeakyReLU
from keras.models import Sequential
from keras.optimizers import SGD, Adam, Nadam
from keras.regularizers import l2

from errors import JamlError


def model_DNN_classifier(input_dim, num_hidden=(1024, 1024, 1024),
                         num_labels=1, dropout=0.5, beta=0.01, l_rate=0.01, momentum=0.9,
                         init_mode='he_normal', optimizer='SGD', activation='relu', activation_out='sigmoid',
                         model_summary=True) -> Sequential:

    dropout = float(dropout)
    beta = float(beta)

    if activation == 'relu':
        act = 'relu'
    elif activation == 'tanh':
        act = 'tanh'
    elif activation == 'LeakyReLU':
        act = LeakyReLU()
    else:
        raise JamlError("I can't use this activation function to compile a DNN")

    model = Sequential(name='model_' + str(len(num_hidden)) + '_layers')
    model.add(Dense(output_dim=num_hidden[0], kernel_initializer=init_mode, input_dim=input_dim,
                    W_regularizer=l2(l=beta), name='Dense_1'))
    model.add(Activation(act))
    model.add(Dropout(dropout, name='DropOut_1'))

    for idx in range(len(num_hidden) - 1):
        model.add(Dense(output_dim=num_hidden[idx + 1], kernel_initializer=init_mode,
                        W_regularizer=l2(l=beta), name='Dense_' + str(idx + 2)))
        if activation == 'LeakyReLU':
            act = LeakyReLU(input_shape=(num_hidden[idx + 1],))

        model.add(Activation(act))
        model.add(Dropout(dropout, name='DropOut_' + str(idx + 2)))

    model.add(Dense(output_dim=num_labels, kernel_initializer=init_mode,
                    activation=activation_out, W_regularizer=l2(l=beta), name='Output'))

    if optimizer == 'SGD':
        opt = SGD(lr=l_rate, momentum=momentum, nesterov=True)
    elif optimizer == 'Adam':
        opt = Adam(lr=l_rate)
    elif optimizer == 'Nadam':
        opt = Nadam(lr=l_rate)
    else:
        raise JamlError("I don't know the %s optimizer" % optimizer)

    if model_summary:
        model.summary()

    model.compile(loss='binary_crossentropy', metrics=['binary_crossentropy', 'accuracy'],  # removed f1 score
                  optimizer=opt)
    return model


class BatchLogger(Callback):
    def __init__(self, display):
        """
        display: display progress every 5%
        """
        # Callback.__init__(self)
        super().__init__()
        self.seen = 0
        self.display = display

"""
This is a implementation of forward prop layers.
There are some notations. 
N is batch size.
L is spacial size of feature vector (196)
D is dimension of image feature vector (512)
T is the number of time step which is equal to (length of each caption) - 1.
V is vocabulary size. 
M is dimension of word vector which is embedding size.
H is dimension of hidden state.
"""
import tensorflow as tf


def init_lstm(X, W1, b1, W2, b2, use_dropout=False):
    """
    Inputs:
    - X: mean feature vector of shape (N, D).
    - W1: weights of shape (D, H).
    - b1: biases of shape (H,).
    - W2: weights of shape (D, H).
    - b2: biases of shape (H,).
    - use_dropout: True if using drop-out
    Returns:
    - out: output data of shape (N, H).
    """
    h = affine_relu_forward(X, W1, b1)
    if use_dropout:
        h = tf.nn.dropout(h, 0.5)
    out = affine_tanh_forward(h, W2, b2)
    return out


def word_embedding_forward(X, W_embed):
    """
    Inputs:
    - X: input caption data (contains word index) for entire timeseries of shape (N, T) or single time step of shape (N,).
    - W_embed: embedding matrix of shape (V, M).
    Returns:
    - out: word vector of shape (N, T, M) or (N, M).
    """
    out = tf.nn.embedding_lookup(W_embed, X)
    return out


def project_feature(X, W):
    """
    Inputs:
    - X: feature vector of shape (N, L, D).
    - W: weights of shape (D, D).
    Returns:
    - out: projected feature vector of shape (N, L, D).
    """
    L = tf.shape(X)[1]
    D = tf.shape(X)[2]
    
    X = tf.reshape(X, [-1, D])
    out =  tf.matmul(X, W) 
    return tf.reshape(out, [-1, L, D])


def attention_forward(X, X_proj, prev_h, W_proj_h, b_proj, W_att):
    """
    Inputs: 
    - X: feature vector of shape (N, L, D)
    - X_proj: projected feature vector of shape (N, L, D)
    - prev_h: previous hidden state of shape (N, H)
    - W_proj_h: weights for projecting(or encoding) previous hidden state of shape (H, D)
    - b_proj: biases for projecting of shape (D,)
    - W_att: weigths for hidden-to-out of shape (D, 1)
    Returns:
    - context: output data (context vector) for soft attention of shape (N, D) 
    - alpha: alpha weights for visualization of shape (N, L)
    """
    L = tf.shape(X)[1]
    D = tf.shape(X)[2]

    h_proj = tf.matmul(prev_h, W_proj_h)   # (N, D)
    h_proj = tf.expand_dims(h_proj, 1)    # (N, 1, D)
    hidden = tf.nn.relu(X_proj + h_proj + b_proj)   # (N, L, D)
    hidden_flat = tf.reshape(hidden, [-1, D])
    out =  tf.matmul(hidden_flat, W_att)   # (N x L, 1)   In this case, we don't need to add bias (because of softmax).
    out =  tf.reshape(out, [-1 ,L])
    alpha = tf.nn.softmax(out)    # (N, L)
    alpha_expand = tf.expand_dims(alpha, 2)    # (N, L, 1)
    context = tf.reduce_sum(X * alpha_expand, 1)    # (N, D)
    return context, alpha


def rnn_step_forward(X, prev_h, context, Wx, Wh, Wz, b):
    """
    Inputs:
    - X: word vector for current time step of shape (N, M).
    - prev_h: previous hidden state of shape (N, H).
    - context: context vector of shape (N, D).
    - Wx: weights for wordvec-to-hidden of shape (M, H).
    - Wh: weights for hidden-to-hidden of shape (H, H).
    - Wz: weights for context-to-hidden of shape(D, H).
    - b: biases of shape (H,).
    Returns:
    - h: hidden states at current time step, of shape (N, H).
    """
    h = tf.nn.tanh(tf.matmul(X, Wx) + tf.matmul(prev_h, Wh) + tf.matmul(context, Wz)) + b
    return h


def lstm_step_forward(X, prev_h, prev_c, context, Wx, Wh, Wz, b):
    """
    Inputs:
    - X: word vector for current time step of shape (N, M).
    - context: context vector of shape (N, D)
    - prev_h: previous hidden state of shape (N, H).
    - prev_c: previous cell state of shape (N, H).
    - Wx: weights for wordvec-to-hidden of shape (M, 4H).
    - Wh: weights for hidden-to-hidden of shape (H, 4H).
    - Wz: weights for context-to-hidden of shape(D, 4H).
    - b: biases of shape (4H,).
    Returns:
    - h: hidden state at current time step, of shape (N, H).
    - c: cell state at current time step, of shape (N, H).
    """

    a = tf.matmul(X, Wx) + tf.matmul(prev_h, Wh) + tf.matmul(context, Wz) + b   
    a_i, a_f, a_o, a_g = tf.split(1, 4, a)
    i = tf.nn.sigmoid(a_i)
    f = tf.nn.sigmoid(a_f)
    o = tf.nn.sigmoid(a_o)
    g = tf.nn.tanh(a_g)

    c = f * prev_c + i * g
    h = o * tf.nn.tanh(c) 
    return h, c
 

def affine_forward(X, W, b):
    """
    Inputs:
    - X: input data of shape (N, H).
    - W: weights of shape (H, V).
    - b: biases of shape (V,).
    Returns:
    - out: output data of shape (N, V).
    """
    out =  tf.matmul(X, W) + b
    return out


def affine_sigmoid_forward(X, W, b):
    """
    Inputs:
    - X: input data of shape (N, H).
    - W: weights of shape (H, V).
    - b: biases of shape (V,).
    Returns:
    - out: output data of shape (N, V).
    """
    out = tf.nn.sigmoid(affine_forward(X, W, b))
    return out


def affine_relu_forward(X, W, b):
    """
    Inputs:
    - X: input data of shape (N, H).
    - W: weights of shape (H, V).
    - b: biases of shape (V,).
    Returns:
    - out: output data of shape (N, V).
    """
    out = tf.nn.relu(affine_forward(X, W, b))
    return out


def affine_tanh_forward(X, W, b):
    """
    Inputs:
    - X: input data of shape (N, H).
    - W: weights of shape (H, V).
    - b: biases of shape (V,).
    Returns:
    - out: output data of shape (N, V).
    """
    out = tf.nn.tanh(affine_forward(X, W, b))
    return out


def softmax_loss(X, y, mask):
    """
    Inputs:
    - X: scores of shape (N, V).
    - y: ground-truth indices of shape (N,) where each element is in the range [0, V).
    - mask: boolean array of shape (N,) where mask[i] tells whether or not the scores at X[i] should contribute to the loss.
    Returns:
    - loss: scalar giving loss
    """
    V =  tf.shape(X)[1]

    y_onehot = tf.cast(tf.one_hot(y, V, on_value=1), tf.float32)
    loss = tf.nn.softmax_cross_entropy_with_logits(X, y_onehot) * tf.cast(mask, tf.float32)    #(N, )
    loss = tf.reduce_sum(loss)
    return loss
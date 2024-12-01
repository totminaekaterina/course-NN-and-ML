# -*- coding: utf-8 -*-
"""3_1_hw.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1vpZpuwsbjGzmt7v1wq_OJPhsHH1UTn6c

# Домашнее задание 2.1

В этом задании вы должны:
1. Написать слой Conv2d на Numpy и определить в нем forward-backward методы
2. Определить слой MaxPool2d
3. Написать всю необходимую обвязку для обучения: оптимизатор с адаптивным шагом и класс, позволяющий изменять расписание для learning rate'а

> Обратите внимание, что в этом задании больше нет тестов.
> Вы должны сами проверять свой код.  
> Это можно сделать так:
> 1. Написать юнит-тесты с помощью Pytorch. То есть, ваш модудь должен повторять поведение torch'а
> 2. Проверять архитектуру не на всем датасете (одна эпоха в наивной имплементации будет занимать около двух часов), а на подвыборке
"""

import numpy as np
import os
import gzip
import urllib.request
import matplotlib.pyplot as plt
from tqdm.auto import tqdm
from IPython.display import clear_output

def load_mnist(flatten=False):
    """Загружает датасет MNIST гитхаба"""

    base_url = "https://raw.githubusercontent.com/golbin/TensorFlow-MNIST/master/mnist/data/"
    filenames = {
        "train_images": "train-images-idx3-ubyte.gz",
        "train_labels": "train-labels-idx1-ubyte.gz",
        "test_images": "t10k-images-idx3-ubyte.gz",
        "test_labels": "t10k-labels-idx1-ubyte.gz"
    }

    def download(filename):
        url = base_url + filename
        print(f"Downloading {filename} from {url}")
        urllib.request.urlretrieve(url, filename)

    def load_mnist_images(filename):
        if not os.path.exists(filename):
            download(filename)
        with gzip.open(filename, 'rb') as f:
            data = np.frombuffer(f.read(), np.uint8, offset=16)
        data = data.reshape(-1, 1, 28, 28)
        print(f"Loaded {filename} with shape {data.shape}")
        return data / np.float32(256)

    def load_mnist_labels(filename):
        if not os.path.exists(filename):
            download(filename)
        with gzip.open(filename, 'rb') as f:
            data = np.frombuffer(f.read(), np.uint8, offset=8)
        print(f"Loaded {filename} with shape {data.shape}")
        return data

    X_train = load_mnist_images(filenames["train_images"])
    y_train = load_mnist_labels(filenames["train_labels"])
    X_test = load_mnist_images(filenames["test_images"])
    y_test = load_mnist_labels(filenames["test_labels"])

    X_train, X_val = X_train[:10000], X_train[10000:]
    y_train, y_val = y_train[:10000], y_train[10000:]

    if flatten:
        X_train = X_train.reshape([X_train.shape[0], -1])
        X_val = X_val.reshape([X_val.shape[0], -1])
        X_test = X_test.reshape([X_test.shape[0], -1])

    if X_train.size == 0 or y_train.size == 0:
        raise ValueError("X_train or y_train is empty")
    if X_val.size == 0 or y_val.size == 0:
        raise ValueError("X_val or y_val is empty")
    if X_test.size == 0 or y_test.size == 0:
        raise ValueError("X_test or y_test is empty")

    return X_train, y_train, X_val, y_val, X_test, y_test

class Layer:
    """A building block.
    Each layer is capable of performing two things:

    - Process input to get output:           output = layer.forward(input)
    - Propagate gradients through itself:    grad_input = layer.backward(input, grad_output)
    Some layers also have learnable parameters which they update during layer.backward.
    """

    def __init__(self, input_units=None, output_units=None, learning_rate=0.01):
        """Here you can initialize layer parameters (if any) and auxiliary stuff."""
        # An identity layer does nothing
        # 1. инициализируем для полносвязного слоя вектор матрицу весов (w) и вектор смещения - bias (b) по формуле: f(x) = xw + и, где x - входной вектор
        # 2. также добавим learning_rate для регилирования размера шага в торону антиградиента для корректировки весов во время обучения

        # количество входных и выходных нейронов в сети
        self.input_units = input_units
        self.output_units = output_units
        self.learning_rate = learning_rate

        if input_units and output_units:
            # learning_rate = 0.01
            self.weights = np.random.randn(input_units, output_units) * 0.01
            self.biases = np.zeros(output_units)

            # Инициализация градиентов для использования в оптимизаторе
            self.grad_weights = np.zeros_like(self.weights)
            self.grad_biases = np.zeros_like(self.biases)

        # хранение активации в forward: хранения входных данных, поступающих в слой на этапе forward, используются потом в backward
        self.last_tensor = None

    def forward(self, input):
        """
        Takes input data of shape [batch, input_units], returns output data [batch, output_units]
        """
        # An identity layer just returns whatever it gets as input.

        self.last_input = input  # сохраняет то что вернул forward для использовния в backward

        return input

    def backward(self, input, grad_output):
        """Performs a backpropagation step through the layer, with respect to the given input.

        To compute loss gradients w.r.t input, you need to apply chain rule (backprop):

        d loss / d x  = (d loss / d layer) * (d layer / d x)

        Luckily, you already receive d loss / d layer as input, so you only need to multiply it by d layer / d x.

        If your layer has parameters (e.g. dense layer), you also need to update them here using d loss / d layer
        """
        # The gradient of an identity layer is precisely grad_output
        input_dim = input.shape[1]

        d_layer_d_input = np.eye(input_dim)

        return np.dot(grad_output, d_layer_d_input)  # chain rule

class ReLU(Layer):
    def __init__(self):
        """ReLU layer simply applies elementwise rectified linear unit to all inputs"""
        pass

    def forward(self, input):
        """Apply elementwise ReLU to [batch, input_units] matrix"""
        output = np.maximum(0, input)  # Применяем ReLU поэлементно по формуле Relu(x) = max(0, x)
        return output

    def backward(self, input, grad_output):
        """Compute gradient of loss w.r.t. ReLU input"""
        relu_grad_mask = input > 0  # true/false. Создаем маску для градиентов, показывает, на какие элементы градиентов нужно воздействовать, а какие оставить нулевыми
        return grad_output * relu_grad_mask  # Умножаем градиенты на маску

class Dense(Layer):
    def __init__(self, input_units, output_units, learning_rate=0.1):  # задали в Layer классе
        """
        A dense layer is a layer which performs a learned affine transformation:
        f(x) =  + b
        """
        super().__init__(input_units, output_units, learning_rate)

    def forward(self, input):
        """
        Perform an affine transformation:
        f(x) = wx + b

        input shape: [batch, input_units]
        output shape: [batch, output units]
        """
        self.last_input = input
        return np.dot(input, self.weights) + self.biases

    def backward(self, input, grad_output):
        """
        Compute the gradients and update the parameters.

        input shape: [batch, input_units]
        grad_output shape: [batch, output_units]
        """
        # Градиент по входу: dL/dX = dL/dY * dY/dX = grad_output * W.T
        grad_input = np.dot(grad_output, self.weights.T)

        # Градиенты по весам и смещениям
        self.grad_weights = np.dot(input.T, grad_output)  # dL/dW = X.T * grad_output
        self.grad_biases = np.sum(grad_output, axis=0)    # dL/db = sum(grad_output)

        # Проверка формы градиентов
        assert self.grad_weights.shape == self.weights.shape and self.grad_biases.shape == self.biases.shape

        # Обновление параметров (шаг градиентного спуска)
        self.weights -= self.learning_rate * self.grad_weights
        self.biases -= self.learning_rate * self.grad_biases

        return grad_input

class Conv2d:
    def __init__(self, in_channels, out_channels, kernel_size, stride=1, padding=0, learning_rate=0.01):
        self.in_channels = in_channels  # Число каналов на входе
        self.out_channels = out_channels  # Число фильтров (ядер свертки)
        self.kernel_size = kernel_size  # Размер матрицы (ядра свертки) [kernel_size, kernel_size]
        self.stride = stride  # Шаг свертки
        self.padding = padding  # Паддинг
        self.learning_rate = learning_rate  # Скорость обучения

        # Инициализация весов и смещений
        self.weights = np.random.randn(out_channels, in_channels, kernel_size, kernel_size) * 0.01
        self.biases = np.zeros(out_channels)

        # Инициализация градиентов
        self.grad_weights = np.zeros_like(self.weights)
        self.grad_biases = np.zeros_like(self.biases)

    def forward(self, x):
        # Получаем размеры входного тензора
        batch_size, in_channels, input_height, input_width = x.shape
        assert in_channels == self.in_channels, "The number of channels at the input does not match the specified number of in_channels"

        # Добавляем нулевой паддинг вокруг входного тензора
        if self.padding > 0:
            x_padded = np.pad(x, ((0, 0), (0, 0), (self.padding, self.padding), (self.padding, self.padding)), mode='constant')
        else:
            x_padded = x

        # Рассчитываем размеры выходного тензора
        output_height = (input_height - self.kernel_size + 2 * self.padding) // self.stride + 1
        output_width = (input_width - self.kernel_size + 2 * self.padding) // self.stride + 1

        # Проверяем, чтобы размеры выходного тензора были положительными
        if output_height <= 0 or output_width <= 0:
            raise ValueError(f"Incorrect dimensions of the output tensor: output_height={output_height}, output_width={output_width}. Possible problems with kernel, stride, and padding parameters")

        # Инициализация выходного тензора
        output = np.zeros((batch_size, self.out_channels, output_height, output_width))

        # Выполняем свертку
        for i in range(output_height):
            for j in range(output_width):
                # Определяем срез, на котором будет применяться фильтр
                start_i = i * self.stride
                end_i = start_i + self.kernel_size
                start_j = j * self.stride
                end_j = start_j + self.kernel_size

                # Проверяем, чтобы размеры не выходили за границы
                if end_i > x_padded.shape[2] or end_j > x_padded.shape[3]:
                    continue

                input_slice = x_padded[:, :, start_i:end_i, start_j:end_j]

                # Умножаем на веса и добавляем смещение
                for k in range(self.out_channels):
                    output[:, k, i, j] = np.sum(input_slice * self.weights[k, :, :, :], axis=(1, 2, 3)) + self.biases[k]

        self.last_input = x  # Сохраняем для backward
        return output

    def backward(self, input, grad_output):
        # Добавляем паддинг к входу
        if self.padding > 0:
            input_padded = np.pad(input, ((0, 0), (0, 0), (self.padding, self.padding), (self.padding, self.padding)), mode='constant')
        else:
            input_padded = input

        grad_input_padded = np.zeros_like(input_padded)  # Градиент по входам
        self.grad_weights = np.zeros_like(self.weights)  # Градиент по весам
        self.grad_biases = np.zeros_like(self.biases)  # Градиент по смещениям

        # Вычисляем градиенты
        for i in range(grad_output.shape[2]):
            for j in range(grad_output.shape[3]):
                start_i = i * self.stride
                end_i = start_i + self.kernel_size
                start_j = j * self.stride
                end_j = start_j + self.kernel_size

                # проверка, чтобы размеры не выходили за границы
                if end_i > input_padded.shape[2] or end_j > input_padded.shape[3]:
                    continue

                input_slice = input_padded[:, :, start_i:end_i, start_j:end_j]

                for k in range(self.out_channels):
                    self.grad_weights[k] += np.sum(input_slice * (grad_output[:, k, i, j])[:, None, None, None], axis=0)
                    self.grad_biases[k] += np.sum(grad_output[:, k, i, j], axis=0)
                    grad_input_padded[:, :, start_i:end_i, start_j:end_j] += self.weights[k] * (grad_output[:, k, i, j])[:, None, None, None]

        # Убираем паддинг из градиента входа
        if self.padding > 0:
            grad_input = grad_input_padded[:, :, self.padding:-self.padding, self.padding:-self.padding]
        else:
            grad_input = grad_input_padded

        return grad_input

class MaxPool2d(Layer):
    """
    Главная цель - уменьшить размерность входного изображения
    """
    def __init__(self, kernel_size, stride=None):
        super().__init__()
        self.kernel_size = kernel_size
        self.stride = stride if stride is not None else kernel_size  # без перекрытия иначе

    def forward(self, x):
        # размеры входного тензора
        batch_size, channels, input_height, input_width = x.shape

        # Проверка, чтобы размеры выходного тензора не стали нулевыми
        assert input_height >= self.kernel_size, f"Error: kernel size {self.kernel_size} is larger than input height {input_height}."
        assert input_width >= self.kernel_size, f"Error: kernel size {self.kernel_size} is larger than input width {input_width}."

        # Корректировка stride, если он превышает размеры входного тензора
        if self.stride > input_height or self.stride > input_width:
            self.stride = min(input_height, input_width)

        # размеры выходного тензора
        output_height = (input_height - self.kernel_size) // self.stride + 1
        output_width = (input_width - self.kernel_size) // self.stride + 1

        # Проверка на возможность корректного вычисления выходных размеров
        if output_height <= 0 or output_width <= 0:
            raise ValueError(f"Invalid output size: height {output_height}, width {output_width}. Check kernel size and stride.")

        output = np.zeros((batch_size, channels, output_height, output_width))  # пока нули для старта

        # Выполняем max pooling
        self.max_indices = np.zeros_like(x, dtype=bool)  # сохраняем индексы максимальных значений для backward
        for i in range(output_height):
            for j in range(output_width):
                # Определяем область для pooling
                region = x[:, :, i * self.stride:i * self.stride + self.kernel_size, j * self.stride:j * self.stride + self.kernel_size]
                # Получаем максимум по каждому региону и сохраняем его
                output[:, :, i, j] = np.max(region, axis=(2, 3))

                # Сохраняем маску с макс значениями для backward
                max_mask = (region == output[:, :, i, j][:, :, None, None])  # для согласования форм
                self.max_indices[:, :, i * self.stride:i * self.stride + self.kernel_size, j * self.stride:j * self.stride + self.kernel_size] = max_mask

        return output

    def backward(self, input, grad_output):
        # хранение градиентов
        grad_input = np.zeros_like(input)

        # Распространяем градиент только по индексам с макс значениями
        for i in range(grad_output.shape[2]):
            for j in range(grad_output.shape[3]):
                grad_input[:, :, i * self.stride:i * self.stride + self.kernel_size, j * self.stride:j * self.stride + self.kernel_size] += \
                    (grad_output[:, :, i, j][:, :, None, None] * self.max_indices[:, :, i * self.stride:i * self.stride + self.kernel_size, j * self.stride:j * self.stride + self.kernel_size])

        return grad_input

class Flatten(Layer):
    """
    Цель - преобразовать многомерный массив - в одномерный
    """
    def forward(self, x):
        """
        Perform an flatten operation:
          input shape: [batch, input_channels, input_height, input_width]
          output shape: [batch, input_channels * output_height * output_width]
        """
        return x.reshape(x.shape[0], -1)

    def backward(self, input, grad_output):
        return grad_output.reshape(input.shape)

def softmax_crossentropy_with_logits(logits,reference_answers):
    """Compute crossentropy from logits[batch,n_classes] and ids of correct answers"""
    # logits имеет dim [batch_size, n_classes]
    # reference_answers - массив, содержащит индексы правильных классов для каждого примера в батче
    logits_for_answers = logits[np.arange(len(logits)),reference_answers]

    # формула кросс-энтропии
    xentropy = - logits_for_answers + np.log(np.sum(np.exp(logits),axis=-1))

    return xentropy


def grad_softmax_crossentropy_with_logits(logits,reference_answers):
    """Compute crossentropy gradient from logits[batch,n_classes] and ids of correct answers"""

    # вычисляет градиент функции потерь кросс-энтропии по логитам - производную функции cross entropy
    ones_for_answers = np.zeros_like(logits)
    ones_for_answers[np.arange(len(logits)),reference_answers] = 1 # правильный класс

    softmax = np.exp(logits) / np.exp(logits).sum(axis=-1,keepdims=True) # получаем вероятность

    return (- ones_for_answers + softmax) / logits.shape[0] # возвращает градиент функции потреь по логитам

"""В имплементации этих двух классов есть небольшие неточности.
Посмотрите, как сделана имплементация метода моментов в Pytorch и добавьте пропущенное.

Если хотите, можете имплементировать какой-нибудь другой оптимизатор - например, AdamW, Sophia, Lion, Adan, LAMB и т.п.

Также можете придумать нестандартный scheduling (подсказка: нестандартные расписания лучше всего искать во вполне стандартных научных статьях).

За это будут дополнительные баллы. Но обязательно нужно сравнить имплементированный вами оптимизатор со стандартным SGD и методом мом

> Добавлять моменты Нестерова не нужно!
"""

class SGDOptimizer:
    def __init__(self, learning_rate=0.01, momentum=0.0, weight_decay=0.0):
        self.learning_rate = learning_rate
        self.momentum = momentum
        self.weight_decay = weight_decay
        self.momentum_buffer = None

    def step(self, weights, grad_weights, lr=None):
        """Update weights or biases based on gradient"""
        if lr is None:
            lr = self.learning_rate

        # Если градиенты и веса имеют разные размерности, обновляем отдельно (для весов и смещений)
        if weights.shape != grad_weights.shape:
            raise ValueError(f"Incompatible shapes for weights and gradients: {weights.shape} and {grad_weights.shape}")

        # Если используется momentum
        if self.momentum > 0:
            if self.momentum_buffer is None:
                self.momentum_buffer = np.zeros_like(weights)

            # Обновление буфера моментума
            self.momentum_buffer = self.momentum * self.momentum_buffer + (1 - self.weight_decay) * grad_weights

            # Обновление весов
            weights -= lr * self.momentum_buffer
        else:
            # Обновление без momentum
            weights -= lr * grad_weights

        return weights

class LRScheduler:
    def __init__(self, lr, decay_type='linear', decay_rate=0.1, decay_steps=10):
        """
        Wrapper which performs learning rate updates.

        Args:
            lr (float): Initial learning rate.
            decay_type (str): Type of decay ('linear' or 'exponential').
            decay_rate (float): Rate of decay.
            decay_steps (int): Frequency of applying decay.
        """
        self.lr = lr
        self.decay_type = decay_type
        self.decay_rate = decay_rate
        self.decay_steps = decay_steps
        self.current_step = 0

    def get_lr(self):
        """
        Update learning rate for current iteration based on decay strategy.
        """
        if self.decay_type == 'linear':
            # Linear decay
            current_lr = self.lr / (1 + self.decay_rate * self.current_step / self.decay_steps)

        elif self.decay_type == 'exponential':
            # Exponential decay
            current_lr = self.lr * (self.decay_rate ** (self.current_step / self.decay_steps))

        elif self.decay_type == 'cosine':
            # Cosine annealing
            current_lr = self.lr * (0.5 * (1 + np.cos(np.pi * self.current_step / self.decay_steps)))

        else:
            raise ValueError(f"Unknown decay '{self.decay_type}'. Possible: 'linear', 'exponential', 'cosine'.")

        self.current_step += 1
        return current_lr

X_train, y_train, X_val, y_val, X_test, y_test = load_mnist(flatten=False)

plt.figure(figsize=[6,6])
for i in range(4):
    plt.subplot(2,2,i+1)
    plt.title("Label: %i"%y_train[i])
    plt.imshow(X_train[i].reshape([28,28]),cmap='gray');

network = []
hidden_layers_size = 10

# Convolutional and pooling layers
network.append(Conv2d(1, 8, kernel_size=5, stride=1, padding=2))  # Output: (batch, 8, 28, 28)
network.append(MaxPool2d(kernel_size=2, stride=2))                # Output: (batch, 8, 14, 14)
network.append(ReLU())

network.append(Conv2d(8, 16, kernel_size=5, stride=1, padding=2)) # Output: (batch, 16, 14, 14)
network.append(MaxPool2d(kernel_size=2, stride=2))                # Output: (batch, 16, 7, 7)
network.append(ReLU())

# Flatten layer to convert output to 1D for the Dense layer
network.append(Flatten())

# Fully connected Dense layer with adjusted input dimensions
network.append(Dense(16 * 7 * 7, 10))  # 16 channels * 7 height * 7 width

# Learning rate and optimizers
learning_rate = 0.1
optimizer = SGDOptimizer()
scheduler = LRScheduler(learning_rate)

def forward_with_tests(network, X):
    """
    Compute activations of all network layers by applying them sequentially.
    Return a list of activations for each layer.
    Make sure last activation corresponds to network logits.
    Add tests to verify output sizes at each layer.
    """
    activations = []
    input = X

    # forward with tests
    for idx, layer in enumerate(network):
        print(f"Input shape before layer {idx} ({layer.__class__.__name__}): {input.shape}")

        # Проверка корректности входных данных
        assert input.size > 0, f"Error: Layer {idx} ({layer.__class__.__name__}) received an empty input"

        # Проверка размерностей входных данных в зависимости от типа слоя
        if isinstance(layer, (Conv2d, MaxPool2d, ReLU)):
            assert len(input.shape) == 4, f"Error: Layer {idx} ({layer.__class__.__name__}) received input with incorrect dimensions. Expected 4D tensor, got {len(input.shape)}D"
            if isinstance(layer, Conv2d):
                assert input.shape[1] == layer.in_channels, f"Error: Layer {idx} ({layer.__class__.__name__}) expected {layer.in_channels} channels, but got {input.shape[1]}"
        elif isinstance(layer, (Flatten, Dense)):
            assert len(input.shape) == 2 or len(input.shape) == 4, f"Error: Layer {idx} ({layer.__class__.__name__}) received input with incorrect dimensions. Expected 2D or 4D tensor, got {len(input.shape)}D"

        input = layer.forward(input)
        assert input.size > 0, f"Error: Layer {idx} ({layer.__class__.__name__}) produced an empty output"
        activations.append(input)
        print(f"Output shape after layer {idx} ({layer.__class__.__name__}): {input.shape}")

    assert len(activations) == len(network), "Error: Number of activations does not match number of layers"
    return activations

def train_with_tests(network, X, y, optimizer, lr_scheduler):
    """
    Train your network on a given batch of X and y with additional tests for each layer
    """
    input = X
    activations = []

    # Forward pass with tests
    for idx, layer in enumerate(network):
        # print(f"Input shape before layer {idx} ({layer.__class__.__name__}): {input.shape}")

        # Проверка корректности входных данных
        assert input.size > 0, f"Error: Layer {idx} ({layer.__class__.__name__}) received an empty input"

        # Проверка размерностей входных данных в зависимости от типа слоя
        if isinstance(layer, (Conv2d, MaxPool2d, ReLU)):
            assert len(input.shape) == 4, f"Error: Layer {idx} ({layer.__class__.__name__}) received input with incorrect dimensions. Expected 4D tensor, got {len(input.shape)}D."
            if isinstance(layer, Conv2d):
                assert input.shape[1] == layer.in_channels, f"Error: Layer {idx} ({layer.__class__.__name__}) expected {layer.in_channels} channels, but got {input.shape[1]}."
        elif isinstance(layer, (Flatten, Dense)):
            assert len(input.shape) == 2 or len(input.shape) == 4, f"Error: Layer {idx} ({layer.__class__.__name__}) received input with incorrect dimensions. Expected 2D or 4D tensor, got {len(input.shape)}D."

        input = layer.forward(input)
        assert input.size > 0, f"Error: Layer {idx} ({layer.__class__.__name__}) produced an empty output"
        activations.append(input)
        # print(f"Output shape after layer {idx} ({layer.__class__.__name__}): {input.shape}")

    layer_activations = activations
    layer_inputs = [X] + layer_activations  # layer_input[i] is an input for network[i]
    logits = layer_activations[-1]

    # Compute the loss and the initial gradient
    assert logits.shape[0] == y.shape[0], "Error: Number of logits does not match number of labels"
    loss = softmax_crossentropy_with_logits(logits, y)
    loss_grad = grad_softmax_crossentropy_with_logits(logits, y)

    # Propagate gradients through network layers using .backward
    grad_output = loss_grad
    for i in reversed(range(len(network))):
        grad_output = network[i].backward(layer_inputs[i], grad_output)

    # Update weights and biases with optimizer
    for layer in network:
        if hasattr(layer, 'weights'):
            layer.weights = optimizer.step(layer.weights, layer.grad_weights, lr=lr_scheduler.get_lr())
            layer.biases = optimizer.step(layer.biases, layer.grad_biases, lr=lr_scheduler.get_lr())

    # Update learning rate for the next iteration
    lr_scheduler.get_lr()

    return np.mean(loss)


def iterate_minibatches(inputs, targets, batchsize, shuffle=False):
    assert len(inputs) == len(targets), "Error: Inputs and targets must have the same length"
    if shuffle:
        indices = np.random.permutation(len(inputs))
    for start_idx in tqdm(range(0, len(inputs) - batchsize + 1, batchsize)):
        if shuffle:
            excerpt = indices[start_idx:start_idx + batchsize]
        else:
            excerpt = slice(start_idx, start_idx + batchsize)
        x_batch, y_batch = inputs[excerpt], targets[excerpt]
        assert x_batch.size > 0 and y_batch.size > 0, "Error: Mini-batch is empty"
        yield x_batch, y_batch

# Лог для метрик
train_log, val_log = [], []

for epoch in range(15):
    for x_batch, y_batch in iterate_minibatches(X_train, y_train, batchsize=32, shuffle=True):
        loss = train_with_tests(network, x_batch, y_batch, optimizer, scheduler)

    train_predictions = forward_with_tests(network, X_train)[-1]
    val_predictions = forward_with_tests(network, X_test)[-1]
    train_predicted_classes = np.argmax(train_predictions, axis=1)
    val_predicted_classes = np.argmax(val_predictions, axis=1)

    train_accuracy = np.mean(train_predicted_classes == y_train)
    val_accuracy = np.mean(val_predicted_classes == y_test)

    train_log.append(train_accuracy)
    val_log.append(val_accuracy)

    clear_output()
    print("Epoch", epoch)
    print("Train accuracy:", train_log[-1])
    print("Val accuracy:", val_log[-1])
    plt.plot(train_log, label='train accuracy')
    plt.plot(val_log, label='val accuracy')
    plt.legend(loc='best')
    plt.grid()
    plt.show()
    plt.savefig('epoch.png')






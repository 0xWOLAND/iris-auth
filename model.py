import tensorflow as tf
from tensorflow.keras.layers import (
    Input, Conv2D, MaxPooling2D,
    GlobalAveragePooling2D, Dense,
    RandomFlip, RandomRotation, Concatenate,
    Reshape, Multiply, Permute
)
from tensorflow.keras.models import Model

def attention_block(x, g, inter_channel):
    theta_x = Conv2D(inter_channel, (1, 1), strides=(1, 1))(x)
    phi_g = Conv2D(inter_channel, (1, 1), strides=(1, 1))(g)
    
    f = tf.keras.layers.Activation('relu')(tf.keras.layers.add([theta_x, phi_g]))
    psi_f = Conv2D(1, (1, 1), strides=(1, 1))(f)
    
    rate = tf.keras.layers.Activation('sigmoid')(psi_f)
    return Multiply()([x, rate])

def build_iris_regressor(input_shape=(256, 64, 1), seg_model_path="models/unet_model.h5"):
    # Create two input layers for the iris pair
    inp1 = Input(shape=input_shape, name='iris1')
    inp2 = Input(shape=input_shape, name='iris2')
    
    # Concatenate the segmented images
    x = Concatenate(axis=2)([inp1, inp2])  # Concatenate along width dimension
    
    # ── augmentation ──
    x = RandomFlip('horizontal')(x)
    x = RandomRotation(0.05)(x)
    
    # ── conv 5×5 →11 → pool 2×2 ──
    x = Conv2D(11, (5,5), padding='same', activation='relu')(x)
    x = MaxPooling2D(pool_size=(2,2), strides=(2,2))(x)
    
    # ── attention ──
    x = attention_block(x, x, 11)
    
    # ── conv 3×3 →22 → pool 2×2 ──
    x = Conv2D(22, (3,3), padding='same', activation='relu')(x)
    x = MaxPooling2D(pool_size=(2,2), strides=(2,2))(x)
    
    # ── conv 3×3 →51 → pool 1×2 ──
    x = Conv2D(51, (3,3), padding='same', activation='relu')(x)
    x = MaxPooling2D(pool_size=(1,2), strides=(1,2))(x)
    
    # ── conv 3×3 →28 → pool 1×3 ──
    x = Conv2D(28, (3,3), padding='same', activation='relu')(x)
    x = MaxPooling2D(pool_size=(1,3), strides=(1,3))(x)
    
    # ── conv 3×3 →8 ──
    x = Conv2D(8, (3,3), padding='same', activation='relu')(x)
    
    # ── conv 3×3 →68 ──
    x = Conv2D(68, (3,3), padding='same', activation='relu')(x)
    
    # ── global pooling + FC → regression ──
    x = GlobalAveragePooling2D()(x)
    out = Dense(1, activation='linear', name='regression')(x)
    
    return Model([inp1, inp2], out, name='IrisPairRegressor')

# Example usage:
model = build_iris_regressor((256, 64, 1))
model.summary()

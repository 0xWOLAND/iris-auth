import numpy as np
from sklearn.model_selection import train_test_split
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau

from preprocess import load_dataset, IrisSegmentation
from model import build_iris_regressor

def main():
    # Load models and data
    segmenter = IrisSegmentation("models/unet_model.h5")
    X1, X2, y = load_dataset("dataset", segmenter)
    X1, X2 = X1[..., None], X2[..., None]  # add channel dim

    # Split data
    x1_train, x1_val, x2_train, x2_val, y_train, y_val = train_test_split(
        X1, X2, y, test_size=0.3, random_state=42
    )

    # Build and train model
    model = build_iris_regressor(input_shape=X1.shape[1:], seg_model_path="models/unet_model.h5")
    model.compile(optimizer=Adam(1e-3), loss="mse", metrics=["mae"])

    model.fit(
        [x1_train, x2_train], y_train,
        validation_data=([x1_val, x2_val], y_val),
        epochs=200,
        batch_size=32,
        callbacks=[
            EarlyStopping(monitor="val_loss", patience=10, restore_best_weights=True),
            ModelCheckpoint("best_regressor.h5", monitor="val_loss", save_best_only=True),
            ReduceLROnPlateau(monitor="val_loss", factor=0.1, patience=5, verbose=1)
        ],
        verbose=2
    )

    model.save("final_best_regressor.h5")

if __name__ == "__main__":
    main()

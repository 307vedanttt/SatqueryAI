from pathlib import Path
import logging

import numpy as np
import tensorflow as tf
from PIL import Image


logger = logging.getLogger(__name__)

IMG_SIZE = 256


def preprocess_image(image_path: str) -> np.ndarray:
    """
    Load and preprocess an image for the trained
    Siamese ResNet50 change detection model.

    The trained model contains ResNet50 preprocess_input
    internally, so the image is returned in the 0-255 range.

    Returns:
        numpy array with shape:
        (1, 256, 256, 3)
    """

    image_path = Path(image_path)

    if not image_path.exists():
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    image = Image.open(image_path).convert("RGB")

    image = image.resize(
        (IMG_SIZE, IMG_SIZE),
        Image.Resampling.BILINEAR
    )

    image = np.asarray(
        image,
        dtype=np.float32
    )

    # IMPORTANT:
    # Do NOT divide by 255 here because the trained
    # ResNet50 model already applies preprocess_input.
    #
    # Input remains in the 0-255 range.

    image = np.expand_dims(
        image,
        axis=0
    )

    return image


class ChangeDetectionModel:
    """
    Wrapper around the trained Siamese ResNet50
    change detection model.
    """

    def __init__(self, model_path=None):

        project_root = Path(
            __file__
        ).resolve().parents[2]

        if model_path is None:
            model_path = (
                project_root
                / "models"
                / "weights"
                / "change"
                / "levir_siamese_resnet50.keras"
            )

        self.model_path = Path(model_path)

        if not self.model_path.exists():
            raise FileNotFoundError(
                "Change detection model not found.\n"
                f"Expected location:\n"
                f"{self.model_path}"
            )

        logger.info(
            "Loading change detection model from %s",
            self.model_path
        )

        try:
            # safe_mode=False is useful when the saved model
            # contains a Lambda layer used for absolute difference.
            self.model = tf.keras.models.load_model(
                self.model_path,
                compile=False,
                safe_mode=False
            )

        except TypeError:
            # Compatibility with older TensorFlow/Keras versions
            self.model = tf.keras.models.load_model(
                self.model_path,
                compile=False
            )

        logger.info(
            "Change detection model loaded successfully."
        )

        logger.info(
            "Model input: %s",
            self.model.input_shape
        )

        logger.info(
            "Model output: %s",
            self.model.output_shape
        )

    def predict(
        self,
        image_a: np.ndarray,
        image_b: np.ndarray
    ) -> np.ndarray:
        """
        Generate a pixel-level change probability map.

        Args:
            image_a:
                Before image.
                Shape: (1, 256, 256, 3)

            image_b:
                After image.
                Shape: (1, 256, 256, 3)

        Returns:
            Change probability map.
            Shape: (256, 256)
            Values: 0.0 - 1.0
        """

        prediction = self.model.predict(
            [image_a, image_b],
            verbose=0
        )

        prediction = np.asarray(
            prediction,
            dtype=np.float32
        )

        # Expected:
        # (1, 256, 256, 1)

        if prediction.ndim == 4:
            prediction = prediction[0]

        if prediction.ndim == 3:
            prediction = prediction[:, :, 0]

        prediction = np.clip(
            prediction,
            0.0,
            1.0
        )

        return prediction

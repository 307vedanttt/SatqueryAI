import logging
from pathlib import Path

from schemas.contracts import (
    SpecialistRequest,
    SpecialistResponse
)

from models.change.encoder import (
    ChangeDetectionModel,
    preprocess_image
)

from models.change.difference import (
    calculate_change_percentage,
    calculate_change_confidence,
    calculate_change_statistics
)

from models.change.change_map import (
    save_change_map,
    save_probability_map,
    save_change_overlay
)


logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------

_model = None


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

CHANGE_THRESHOLD = 0.30

# Minimum percentage of changed pixels required before
# saying that meaningful change was detected.
CHANGE_DETECTION_PERCENTAGE = 1.0


# ---------------------------------------------------------
# Model loader
# ---------------------------------------------------------

def get_model():
    """
    Load the trained change detection model once.

    The model remains in memory for subsequent requests.
    """

    global _model

    if _model is None:

        logger.info(
            "Initializing LEVIR-CD Siamese ResNet50 model..."
        )

        _model = ChangeDetectionModel()

        logger.info(
            "LEVIR-CD model initialized successfully."
        )

    return _model


# ---------------------------------------------------------
# Main specialist function
# ---------------------------------------------------------

def run_change_detection(
    request: SpecialistRequest
) -> SpecialistResponse:
    """
    Run satellite image change detection.

    Expected input:
        Exactly two images.

    Image 1:
        Before image.

    Image 2:
        After image.

    Output:
        Change probability map
        Binary change map
        Change percentage
        Confidence
    """

    # -----------------------------------------------------
    # Validate number of images
    # -----------------------------------------------------

    if len(request.images) != 2:

        return SpecialistResponse(
            task=(
                request.task_hint
                if request.task_hint
                else "change_detection"
            ),

            answer=(
                "Exactly 2 satellite images are required "
                "for change detection."
            ),

            confidence=0.0,

            confidence_tier="low",

            bounding_boxes=[],

            evidence=[],

            model_used=(
                "Siamese ResNet50 + decoder "
                "(LEVIR-CD)"
            ),

            status="error",

            error_message=(
                "Exactly 2 images are required."
            )
        )

    try:

        # -------------------------------------------------
        # Get image paths
        # -------------------------------------------------

        img1_path = request.images[0].file_path
        img2_path = request.images[1].file_path

        logger.info(
            "Change detection input A: %s",
            img1_path
        )

        logger.info(
            "Change detection input B: %s",
            img2_path
        )

        # -------------------------------------------------
        # Preprocess
        # -------------------------------------------------

        image_a = preprocess_image(
            img1_path
        )

        image_b = preprocess_image(
            img2_path
        )

        # -------------------------------------------------
        # Load trained model
        # -------------------------------------------------

        model = get_model()

        # -------------------------------------------------
        # Predict
        # -------------------------------------------------

        change_probability = model.predict(
            image_a,
            image_b
        )

        logger.info(
            "Change probability map generated."
        )

        logger.info(
            "Prediction shape: %s",
            change_probability.shape
        )

        # -------------------------------------------------
        # Calculate statistics
        # -------------------------------------------------

        statistics = calculate_change_statistics(
            change_probability,
            threshold=CHANGE_THRESHOLD
        )

        change_percentage = (
            statistics["change_percentage"]
        )

        confidence = (
            statistics["changed_pixel_confidence"]
        )

        mean_probability = (
            statistics["mean_change_probability"]
        )

        max_probability = (
            statistics["max_change_probability"]
        )

        # -------------------------------------------------
        # Determine whether meaningful change exists
        # -------------------------------------------------

        change_detected = (
            change_percentage
            >= CHANGE_DETECTION_PERCENTAGE
        )

        # -------------------------------------------------
        # Confidence tier
        # -------------------------------------------------

        if confidence >= 0.75:

            confidence_tier = "high"

        elif confidence >= 0.50:

            confidence_tier = "moderate"

        else:

            confidence_tier = "low"

        # -------------------------------------------------
        # Generate natural language answer
        # -------------------------------------------------

        if change_detected:

            answer = (
                "Change detected between the two "
                "satellite images. "
                f"Approximately {change_percentage:.2f}% "
                "of the analyzed image area is classified "
                "as changed."
            )

        else:

            answer = (
                "No significant change was detected "
                "between the two satellite images. "
                f"Approximately {change_percentage:.2f}% "
                "of the analyzed area is classified "
                "as changed."
            )

        # -------------------------------------------------
        # Handle change VQA
        # -------------------------------------------------

        if request.task_hint == "change_vqa":

            answer += (
                f"\n\nRegarding your question "
                f"'{request.query}': "
            )

            if change_detected:

                answer += (
                    "The change-detection model found "
                    "evidence of modification between "
                    "the two images."
                )

            else:

                answer += (
                    "The change-detection model found "
                    "limited evidence of modification."
                )

        # -------------------------------------------------
        # Create output directory
        # -------------------------------------------------

        project_root = (
            Path(__file__)
            .resolve()
            .parents[2]
        )

        output_dir = (
            project_root
            / "data"
            / "outputs"
            / "change_detection"
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        # -------------------------------------------------
        # Output paths
        # -------------------------------------------------

        binary_map_path = (
            output_dir
            / "change_map.png"
        )

        probability_map_path = (
            output_dir
            / "change_probability.png"
        )

        overlay_path = (
            output_dir
            / "change_overlay.png"
        )

        # -------------------------------------------------
        # Save maps
        # -------------------------------------------------

        save_change_map(
            change_probability,
            str(binary_map_path),
            threshold=CHANGE_THRESHOLD
        )

        save_probability_map(
            change_probability,
            str(probability_map_path)
        )

        save_change_overlay(
            img2_path,
            change_probability,
            str(overlay_path),
            threshold=CHANGE_THRESHOLD
        )

        logger.info(
            "Change map saved: %s",
            binary_map_path
        )

        # -------------------------------------------------
        # Return SpecialistResponse
        # -------------------------------------------------

        return SpecialistResponse(

            task=(
                request.task_hint
                if request.task_hint
                else "change_detection"
            ),

            answer=answer,

            confidence=float(
                confidence
            ),

            confidence_tier=confidence_tier,

            bounding_boxes=[],

            evidence=[],

            model_used=(
                "Siamese ResNet50 + decoder "
                "(LEVIR-CD)"
            ),

            status="success",

            error_message=None
        )

    except Exception as e:

        logger.exception(
            "Error in change detection"
        )

        return SpecialistResponse(

            task=(
                request.task_hint
                if request.task_hint
                else "change_detection"
            ),

            answer=(
                f"Change detection failed: {str(e)}"
            ),

            confidence=0.0,

            confidence_tier="low",

            bounding_boxes=[],

            evidence=[],

            model_used=(
                "Siamese ResNet50 + decoder "
                "(LEVIR-CD)"
            ),

            status="error",

            error_message=str(e)
        )
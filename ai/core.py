from ai.translator.engine import ai_translate

from ai.translator.learner import learn_translation

from ai.moderation.moderator import auto_approve

from ai.datasets.builder import save_patch

from handler.asset import load_models

from handler.bbox import get_patch


class NomNaAI:

    def __init__(self):

        self.det_model, self.rec_model = load_models()

    # =========================
    # DETECT TEXT
    # =========================
    def detect(
        self,
        image
    ):

        return self.det_model.predict_one_page(
            image
        )

    # =========================
    # OCR
    # =========================
    def recognize(
        self,
        patch,
        top_k=5
    ):

        return self.rec_model.predict_top_k(
            patch,
            top_k=top_k
        )

    # =========================
    # TRANSLATE
    # =========================
    def translate(
        self,
        text
    ):

        return ai_translate(text)

    # =========================
    # LEARN
    # =========================
    def learn(
        self,
        patch,
        ocr_text,
        corrected_text,
        confidence,
        meaning,
        poetry
    ):

        # moderation
        result = auto_approve(
            ocr_text,
            corrected_text,
            confidence
        )

        status = result["status"]

        # save dataset
        save_patch(
            patch,
            corrected_text,
            status
        )

        # learn translation
        learn_translation(
            corrected_text,
            meaning,
            poetry
        )

        return status
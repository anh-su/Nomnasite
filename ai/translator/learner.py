from ai.translator.memory import save_memory


def learn_translation(
    nom_text,
    meaning,
    poetry
):

    if not nom_text:
        return

    save_memory(
        nom_text,
        meaning,
        poetry
    )
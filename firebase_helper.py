import firebase_admin
from firebase_admin import firestore, credentials
from os.path import join, dirname
import time

# init firestore
cred = credentials.Certificate(join(dirname(__file__), "service_account.json"))
app = firebase_admin.initialize_app(cred)
db = firestore.client()


def create_user_if_not_exists(guild_id: int, player_id: int) -> bool:
    """
    Creates a new document with a blank template for a new user.
    Returns true if a document was made, returns false if not
    """
    # Template for a new document
    TEMPLATE = {
        "elo": 0,
        "ign": None,
        "last_tested": {"axe": -1, "sword": -1, "neth_pot": -1, "crystal": -1},
        "losses": -1,
        "wins": -1,
        "ranks": {"axe": 0, "sword": 0, "neth_pot": 0, "crystal": 0},
    }
    # Check if the document exists
    doc_ref = db.collection(str(guild_id)).document(str(player_id))
    doc = doc_ref.get()
    if not doc.exists:
        doc_ref.set(TEMPLATE)
        return True
    else:
        return False


def get_ranks(guild_id: int, player_id: int) -> dict:
    """
    Get's the player's ranks, in a dict format where the key is the kit,
    in snake case, while the pair is the rank, where 0 is lt5 and 10 is ht1
    """
    # Check if the document exists
    create_user_if_not_exists(guild_id, player_id)

    doc_ref = db.collection(str(guild_id)).document(str(player_id))
    doc = doc_ref.get()

    return doc.to_dict()["ranks"]


def set_rank(guild_id: int, player_id: int, kit: str, tier: int):
    """
    Given a kit and a tier, it will update the database such that the player has this
    rank.
    """
    # Check if the document exists
    create_user_if_not_exists(guild_id, player_id)
    doc_ref = db.collection(str(guild_id)).document(str(player_id))

    formatted_kit = kit.replace(" ", "_").lower().strip()
    doc_ref.update({f"ranks.{formatted_kit}": tier})

    # We also need to update the last_tested field
    doc_ref.update({f"last_tested.{formatted_kit}": time.time()})

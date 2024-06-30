import firebase_admin
from firebase_admin import firestore, credentials
from os.path import join, dirname
import time

# init firestore
cred = credentials.Certificate(join(dirname(dirname(__file__)), "service_account.json"))
app = firebase_admin.initialize_app(cred)
db = firestore.client()


def create_user_if_not_exists(
    guild_id: int, player_id: int, avatar_url: str, name: str
) -> bool:
    """
    Creates a new document with a blank template for a new user.
    Returns true if a document was made, returns false if not
    """
    # Template for a new document
    TEMPLATE = {
        "elo": 0,
        "ign": name,
        "avatar_url": avatar_url,
        "last_tested": {
            "axe": -1,
            "sword": -1,
            "neth_pot": -1,
            "crystal": -1,
            "dia_pot": -1,
            "uhc": -1,
            "smp": -1,
        },
        "losses": -1,
        "wins": -1,
        "ranks": {
            "axe": 0,
            "sword": 0,
            "neth_pot": 0,
            "crystal": 0,
            "dia_pot": 0,
            "uhc": 0,
            "smp": 0,
        },
        "highest_rank": 0,
    }
    # Check if the document exists
    doc_ref = db.collection(str(guild_id)).document(str(player_id))
    doc = doc_ref.get()
    if not doc.exists:
        doc_ref.set(TEMPLATE)
        return True
    else:
        return False


def get_ranks(guild_id: int, player_id: int, avatar_url: str, name: str) -> dict:
    """
    Get's the player's ranks, in a dict format where the key is the kit,
    in snake case, while the pair is the rank, where 0 is lt5 and 10 is ht1
    """
    # Check if the document exists
    create_user_if_not_exists(guild_id, player_id, avatar_url, name)

    doc_ref = db.collection(str(guild_id)).document(str(player_id))
    doc = doc_ref.get()

    return doc.to_dict()["ranks"]  # type: ignore


def set_rank(
    guild_id: int, player_id: int, kit: str, tier: int, avatar_url: str, name: str
):
    """
    Given a kit and a tier, it will update the database such that the player has this
    rank.
    """
    # Check if the document exists
    create_user_if_not_exists(guild_id, player_id, avatar_url, name)
    doc_ref = db.collection(str(guild_id)).document(str(player_id))

    formatted_kit = kit.replace(" ", "_").lower().strip()
    doc_ref.update({f"ranks.{formatted_kit}": tier})

    # We also need to update the last_tested field
    doc_ref.update({f"last_tested.{formatted_kit}": time.time()})
    set_highest_rank(guild_id, player_id, avatar_url, name)

    # We also need to update the user's elo
    update_elo(guild_id, player_id)


def update_elo(guild_id: int, player_id: int):
    """
    Updates the ELO of the player by adding up the INTEGER values of each tier multiplied by 2
    NOTE: Assumes that the player with id player_id already exists in the db. Make sure to call create_user_if_not_exists() before this.
    """
    # Get the ranks of this player
    doc_ref = db.collection(str(guild_id)).document(str(player_id))

    data = doc_ref.get().to_dict()
    ranks = data["ranks"]  # type: ignore

    total_elo = 0
    for k, v in ranks.items():
        total_elo += int(v) * 2
    doc_ref.update({"elo": total_elo})


def get_elo(guild_id: int, player_id: int, avatar_url: str, name: str) -> int:
    """
    Retrieves the players ELO (computed overall ranking).
    IF player does not exists in the DB, new document will be created and this function will return 0 (as they have 0 ELO)
    """
    # Make sure the user exists
    create_user_if_not_exists(guild_id, player_id, avatar_url, name)
    doc_ref = db.collection(str(guild_id)).document(str(player_id))
    data = doc_ref.get().to_dict()
    elo = data["elo"]  # type: ignore
    return int(elo)


def remove_rank(guild_id: int, player_id: int, kit: str, avatar_url: str, name: str):
    """
    Sets a person's rank to 0 and when they were tested back to -1, essentially resetting them
    """
    # Make sure the user exists
    create_user_if_not_exists(guild_id, player_id, avatar_url, name)
    doc_ref = db.collection(str(guild_id)).document(str(player_id))
    formatted_kit = kit.replace(" ", "_").lower().strip()

    doc_ref.update({f"ranks.{formatted_kit}": 0})
    doc_ref.update({f"last_tested.{formatted_kit}": -1})

    # Update ELO
    update_elo(guild_id, player_id)
    # Update Highest Rank
    set_highest_rank(guild_id, player_id, avatar_url, name)


def get_last_tested(
    guild_id: int, player_id: int, kit: str, avatar_url: str, name: str
) -> int:
    """
    Get the number, in days, since a player was tested in a given kit.
    """

    # Check if document exists
    create_user_if_not_exists(guild_id, player_id, avatar_url, name),
    doc_ref = db.collection(str(guild_id)).document(str(player_id))

    formatted_kit = kit.replace(" ", "_").lower().strip()
    doc = doc_ref.get()
    doc = doc.to_dict()
    last_time = doc["last_tested"][formatted_kit]  # type: ignore
    total_time = time.time() - last_time
    total_time = total_time // 90000  # Convert from seconds to days
    return total_time


def set_highest_rank(guild_id: int, player_id: int, avatar_url: str, name: str):
    create_user_if_not_exists(guild_id, player_id, avatar_url, name)
    doc_ref = db.collection(str(guild_id)).document(str(player_id))
    doc = doc_ref.get()
    doc = doc.to_dict()

    m = 0
    for i in doc["ranks"].values():  # type: ignore
        m = max(m, i)

    doc_ref.update({"highest_rank": m})


def get_highest_rank(guild_id: int, player_id: int, avatar_url: str, name: str):
    create_user_if_not_exists(guild_id, player_id, avatar_url, name)
    doc_ref = db.collection(str(guild_id)).document(str(player_id))
    doc = doc_ref.get()
    doc = doc.to_dict()
    return doc["highest_rank"]  # type: ignore


def get_leaderboard(guild_id: int) -> tuple[int, str, str]:
    """
    Gets the following details about the top 10 players in the guild:
    -discord id
    -highest kit
    -highest rank
    """
    ids = []
    kits = []
    ranks = []
    coll_ref = db.collection(str(guild_id))
    query = coll_ref.order_by("elo", direction=firestore.Query.DESCENDING).limit(10)  # type: ignore
    results = query.get()
    print(f"Got query results!")
    for i in results:
        data = i
        print(f"Top 10 Raw Data: {data}")
        id = i.id
        data = data.to_dict()
        # Get the kit
        kit = ""
        m = 0
        for k, v in data["ranks"].items():  # type: ignore
            if v > m:
                kit = k
                m = v
        rank = data["highest_rank"]  # type: ignore

        ids.append(id)
        kits.append(kit)
        ranks.append(rank)
    return (ids, kits, ranks)  # type: ignore

from typing import Dict, Literal
import firebase_admin
from firebase_admin import firestore, credentials
from os.path import join, dirname
import time
import discord
from typing import Any
from google.cloud.firestore_v1.base_document import DocumentSnapshot
from google.cloud.firestore_v1.client import Client
from google.cloud.firestore_v1 import FieldFilter
from google.cloud.firestore_v1.document import DocumentReference
from loguru import logger as log

# init firestore
cred = credentials.Certificate(join(dirname(dirname(__file__)), "service_account.json"))
app = firebase_admin.initialize_app(cred)
db: Client = firestore.client()


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


#                   RANKS


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


#                   ELO


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


#                   HIGHEST RANK


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


#                   MISC


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


def get_last_tested(
    guild_id: int, player_id: int, kit: str, avatar_url: str, name: str
) -> int:
    """
    Get the number, in days, since a player was tested in a given kit.
    """

    # Check if document exists
    create_user_if_not_exists(guild_id, player_id, avatar_url, name)
    doc_ref = db.collection(str(guild_id)).document(str(player_id))

    formatted_kit = kit.replace(" ", "_").lower().strip()
    doc = doc_ref.get()
    doc = doc.to_dict()
    last_time = doc["last_tested"][formatted_kit]  # type: ignore
    total_time = time.time() - last_time
    total_time = total_time // 90000  # Convert from seconds to days
    return total_time


#                   TICKETING
def create_ticket(
    userReq: discord.Member,
    isCracked: bool,
    kit: str,
    region: str,
    official_tested: bool,
) -> bool:
    """Creates a document in the firestore DB representing the requested ticket

    Args:
        userReq (discord.Member): The person who requested to be tested
        isCracked (bool): Whether the person is cracked or not
        kit (str): The kit they wish to be tested in, in capital case. e.g, Sword, Neth Pot, Dia Pot
        region (str): The user's region, must be in ["EU", "NA", "AS", "AF"]
        official_tested (bool): Whether the person has been tier tested with MCTiers or not

    Returns:
        bool: True if a new ticket was created, False if this ticket already exists.
    """
    formatted_kit = kit.replace(" ", "_").lower().strip()
    template = {
        "userId": str(userReq.id),
        "isCracked": isCracked,
        "kit": formatted_kit,
        "region": region.upper().strip(),
        "tested_official": official_tested,
        "time_requested": int(time.time()),
    }

    doc_ref = db.collection("tests").document(formatted_kit + str(userReq.id))
    doc_snap = doc_ref.get()

    if not doc_snap.exists:
        doc_ref.set(template)
        return True
    return False


def get_test_info(user_id: int, kit: str) -> Dict[str, Any] | None:
    """Get info about a requested test

    Args:
        user_id (int): The user ID of the person who requested the test
        kit (str): The Unformatted kit - In Capital Case eg. Dia Pot

    Returns:
        Dict[str, Any] | None: The document as a dict, None if the document doesn't exist.
    """
    formatted_kit = kit.replace(" ", "_").lower().strip()
    doc_ref = db.collection("tests").document(formatted_kit + str(user_id))
    doc_snap = doc_ref.get()

    if doc_snap.exists:
        return doc_snap.to_dict()
    return None


#           QUEUE


def get_queue_position(user_id: int, kit: str) -> int:
    """Get the position in queue that a user is in the given kit

    Args:
        user_id (int): The User ID of the person who's position we are to retrieve
        kit (str): The Kit, non-formatted to look in, e.g. Dia Pot

    Returns:
        int: The Position the user is in (1 = first etc.). If 0, then the user did not create a ticket.
    """
    formatted_kit = kit.replace(" ", "_").lower().strip()
    tickets_ref = db.collection("tests")

    docs = (
        tickets_ref.where(filter=FieldFilter("kit", "==", formatted_kit))
        .order_by("time_requested")
        .stream()
    )
    position = 1
    for doc in docs:
        dict_doc = doc.to_dict()
        # TODO: Remove
        if dict_doc == None:
            log.warning("Document found by Query is None!")
            continue

        log.debug(
            f"Document field userId in tickets collection: {int(dict_doc['userId'])}\tUser ID to compare: {user_id}\t\tSame? {int(dict_doc['userId']) == user_id}"
        )

        if int(dict_doc["userId"]) == user_id:
            log.debug(f"Returning Queue position of user to be {position}")
            return position

        position += 1
    log.warning("Didn't find that ticket somehow!")
    return 0


def get_queue(kit: str) -> list[int]:
    """Gets the queue of a kit - a list of user ids waiting for a test, ordered from waiting longest to least

    Args:
        kit (str): The unformatted kit to search for, e.g. Dia Pot

    Returns:
        list[int]: A List of Discord User IDs representing people who have requested a test in this kit, ordered from people waiting the longest to the least.
    """
    formatted_kit = kit.replace(" ", "_").lower().strip()
    tickets_ref = db.collection("tests")

    docs = (
        tickets_ref.where(filter=FieldFilter("kit", "==", formatted_kit))
        .order_by("time_requested")
        .stream()
    )

    output = []
    for doc in docs:
        items: Dict[str, Any] | None = doc.to_dict()
        if items != None:
            output.append(int(items["userId"]))
    return output


def send_to_end_of_queue(kit: str, user_id: int) -> Literal[0] | Literal[1]:
    """Send a person to the end of the queue (by setting their time requested to the current time)

    Args:
        kit (str): The kit they wish to be tested in, unformatted
        user_id (int): The user ID of the person who requested the tier test

    Returns:
        Literal[0] | Literal[1]: 0 if success, 1 if the doc doesn't exist
    """
    kit = kit.strip().lower().replace(" ", "_")
    doc_ref = db.collection("tests").document(f"{kit}{user_id}")
    doc_snap = doc_ref.get()
    if doc_snap.exists:
        doc_ref.update({"time_requested": time.time()})
        return 0
    log.warning(
        f"Ticket Document does not exist! Unable to send to the end of the queue. {kit}{user_id}"
    )
    return 1


def set_test_channel_id(
    kit: str, user_id: int, channel_id: int
) -> Literal[0] | Literal[1]:
    """Set the Discord Channel ID of an opened ticket. ID of 0 = no ticket opened aka. still in queue
    NOTE: The channel ID is saved as a STRING
    Args:
        kit (str): _description_
        user_id (int): _description_
        channel_id (int): _description_

    Returns:
        Literal[0] | Literal[1]: _description_
    """
    kit = kit.strip().lower().replace(" ", "_")
    doc_ref = db.collection("tests").document(f"{kit}{user_id}")
    doc_snap = doc_ref.get()
    if doc_snap.exists:
        doc_ref.update({"channel_id": str(channel_id)})
        return 0
    log.warning(
        f"Ticket Document does not exist! Unable to set channel ID. {kit}{user_id}"
    )
    return 1


#           TESTERS
def add_tester(user: discord.Member, kits_testing: list[bool]) -> bool:
    """Adds a tester to the Firestore Database
    {
        "completed_tests": 0,
        "userId": user.id,
        "activeTests": 0,
        "amountActive": 0,
        "isActive": False,
        "ticket_channel": "0",
        "kits": kits_tested,
        "tickets": {
            "sword": "0",
            "axe": "0",
            "dia_pot": "0",
            "neth_pot": "0",
            "crystal": "0",
            "uhc": "0",
            "smp": "0",
    }

    Args:
        user (discord.Member): The user who will be added as a tester
        kits_testing (tuple[bool]): A "checkbox" of each kit, where the tuple's length must be 7. MUST BE IN THIS ORDER: ["sword", "axe", "dia_pot", "neth_pot", "crystal", "uhc", "smp"]

    Returns:
        bool: True if a tester was added, False if that tester already exists.
    Raises:
        ValueError: If the length of kits_testing is NOT equal to 7
    """
    if len(kits_testing) != 7:
        raise ValueError(
            f"Expected kits_testing to be of length 7, got length {len(kits_testing)}"
        )
    doc_ref: DocumentReference = db.collection("testers").document(str(user.id))

    # Get a list of the kits as strings that the tester tests in
    all_kits = ["sword", "axe", "dia_pot", "neth_pot", "crystal", "uhc", "smp"]

    kits_tested = [i for i, u in zip(all_kits, kits_testing) if u]
    log.debug(f"Kits tested: {kits_tested}")

    template = {
        "completed_tests": 0,
        "userId": user.id,
        "activeTests": 0,
        "amountActive": 0,
        "isActive": False,
        "kits": kits_tested,
        "ticket_channel": "0",
        "tickets": {
            "sword": "0",
            "axe": "0",
            "dia_pot": "0",
            "neth_pot": "0",
            "crystal": "0",
            "uhc": "0",
            "smp": "0",
        },
    }

    # Check if it exists, if it does, return False, if not add the template and return true
    doc_snap = doc_ref.get()
    if doc_snap.exists:
        return False
    else:
        doc_ref.set(template)
        return True


def get_tester(id: int) -> dict | None:
    """Get the firestore document as a dict of a tester. The format is similar to this:
    {
        "completed_tests": 0,
        "userId": user.id,
        "activeTests": 0,
        "amountActive": 0,
        "isActive": False,
        "kits": kits_tested,
        "tickets": {
            "sword": "0",
            "axe": "0",
            "dia_pot": "0",
            "neth_pot": "0",
            "crystal": "0",
            "uhc": "0",
            "smp": "0",
    }

    Args:
        id (int): The tester ID to check for

    Returns:
        dict | None: The document of the tester in the format above, or None if the tester is not in the database.
    """
    doc_ref: DocumentReference = db.collection("testers").document(str(id))
    doc_snap: DocumentSnapshot = doc_ref.get()

    if doc_snap.exists:
        return doc_snap.to_dict()
    else:
        return None


def has_test(id: int, kit: str) -> bool:
    """Check if a tester has a test in a given kit

    Args:
        id (int): The tester's user ID
        kit (str): The kit to check for

    Returns:
        bool: whether the tester has a test ongoing in this kit or not
    """
    doc = get_tester(id)
    formatted_kit = (" ".join(kit.split())).replace(" ", "_").lower()
    return doc["tickets"][formatted_kit] != "0" if doc != None else False


def set_test(tester_id: int, kit: str, ticket_id: int) -> Literal[0] | Literal[1]:
    """Use this to set a reference to the ticket which the tester is testing in a kit

    Args:
        tester_id (int): The tester who is taking this testing request / ticket
        kit (str): The kit that is being tested
        ticket_id (int): This is the user ID of the testee

    Returns:
        Literal[0] | Literal[1]: 0 = Execution successful, 1 = Execution unsuccessful
    """
    doc_ref: DocumentReference = db.collection("testers").document(str(tester_id))
    formatted_kit = kit.replace(" ", "_").lower().strip()
    changes = {f"tickets.{formatted_kit}": ticket_id}

    doc_snap = doc_ref.get()
    if doc_snap.exists:
        doc_ref.update(changes)
        return 0
    else:
        log.warning(
            f"Tester with ID {tester_id} does not have a document. Unable to set test."
        )
        return 1

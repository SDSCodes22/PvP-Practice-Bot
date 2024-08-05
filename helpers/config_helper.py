from os.path import dirname, join
import json


def get_rank_role_id(role: str) -> int:
    """
    Given a role, it will return the role's discord role ID.\n
    Roles:\n
        -`admin`\n
        -`tester`\n
        -`manager`\n
        -`LT5 to HT1`
        -online
        -offline
    """
    config_path: str = join(dirname(dirname(__file__)), "config.json")
    role_id: int = -1
    with open(config_path, "r") as config_file:
        raw_json: dict = json.loads(config_file.read())
        role_id = raw_json["role_ids"][role]
    return int(role_id)


def get_all_rank_role_ids():
    """
    Returns a list of all role ids excluding: admin, tester, manager
    """
    config_path: str = join(dirname(dirname(__file__)), "config.json")
    role_id: int = -1
    roles: list[int] = []
    with open(config_path, "r") as config_file:
        raw_json: dict = json.loads(config_file.read())

        for k, v in raw_json["role_ids"].items():
            if k == "admin" or k == "tester" or k == "manager":
                continue
            roles.append(int(v))

    return roles


def get_test_cooldown() -> int:
    """
    Returns how long (in days) the user must wait between tests in the same kit.\n
    SET THIS VARIABLE IN config.json!
    """
    config_path: str = join(dirname(dirname(__file__)), "config.json")
    role_id: int = -1
    wait_time: int = -1
    with open(config_path, "r") as config_file:
        raw_json: dict = json.loads(config_file.read())
        wait_time = int(raw_json["test_cooldown"])

    return wait_time


def get_results_channel_id() -> int:
    """
    Returns the channel ID of the results channel
    SET THIS VARIABLE IN config.json!
    \n
    \n
    Returns -1 if the channel is not found in config.json
    """
    config_path: str = join(dirname(dirname(__file__)), "config.json")
    role_id: int = -1
    results_channel: int = -1
    with open(config_path, "r") as config_file:
        raw_json: dict = json.loads(config_file.read())
        try:
            results_channel = int(raw_json["results_channel"])
        except:
            print(
                "ERROR: Attribute 'results_channel' not found in config.json. \nUnable to post user's results.\n\n"
            )

    return results_channel


def set_test_cooldown(cooldown: int):
    config_path: str = join(dirname(dirname(__file__)), "config.json")
    with open(config_path, "r") as config_file:
        raw_json: dict = json.loads(config_file.read())

    raw_json["test_cooldown"] = cooldown
    with open(config_path, "w") as config_file:
        json.dump(raw_json, config_file)


def set_results_channel_id(channel_id: int):
    config_path: str = join(dirname(dirname(__file__)), "config.json")
    with open(config_path, "r") as config_file:
        raw_json: dict = json.loads(config_file.read())

    raw_json["results_channel"] = channel_id
    with open(config_path, "w") as config_file:
        json.dump(raw_json, config_file)


def configure_roles(
    admin: int,
    tester: int,
    manager: int,
    lt5: int,
    ht5: int,
    lt4: int,
    ht4: int,
    lt3: int,
    ht3: int,
    lt2: int,
    ht2: int,
    lt1: int,
    ht1: int,
    online: int,
    offline: int,
):
    role_ids = {
        "admin": admin,
        "tester": tester,
        "manager": manager,
        "LT5": lt5,
        "HT5": ht5,
        "LT4": lt4,
        "HT4": ht4,
        "LT3": lt3,
        "HT3": ht3,
        "LT2": lt2,
        "HT2": ht2,
        "LT1": lt1,
        "HT1": ht1,
        "online": online,
        "offline": offline,
    }
    config_path: str = join(dirname(dirname(__file__)), "config.json")
    with open(config_path, "r") as config_file:
        raw_json: dict = json.loads(config_file.read())

    raw_json["role_ids"] = role_ids
    with open(config_path, "w") as config_file:
        json.dump(raw_json, config_file)


def configureCategories(
    sword: int, axe: int, neth_pot: int, dia_pot: int, crystal: int, uhc: int, smp: int
):
    category_ids = {
        "sword": sword,
        "axe": axe,
        "neth_pot": neth_pot,
        "dia_pot": dia_pot,
        "crystal": crystal,
        "uhc": uhc,
        "smp": smp,
    }
    config_path: str = join(dirname(dirname(__file__)), "config.json")
    with open(config_path, "r") as config_file:
        raw_json: dict = json.loads(config_file.read())
    raw_json["ticket_categories"] = category_ids
    with open(config_path, "w") as config_file:
        json.dump(raw_json, config_file)


def getCategories():
    config_path: str = join(dirname(dirname(__file__)), "config.json")
    with open(config_path, "r") as config_file:
        raw_json: dict = json.loads(config_file.read())
    return raw_json["ticket_categories"]


if __name__ == "__main__":
    print(get_rank_role_id("LT4"))
    print(get_all_rank_role_ids())
